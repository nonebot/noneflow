import * as core from '@actions/core'
import * as github from '@actions/github'
import * as exec from '@actions/exec'
import {
  checkCommitType,
  checkLabel,
  checkTitle,
  closeIssue,
  commitandPush,
  createPullRequest,
  extractInfo,
  extractIssueNumberFromRef,
  getPullRequests,
  resolveConflictPullRequests,
  updateFile
} from './utils'

async function run(): Promise<void> {
  try {
    const base: string = core.getInput('base', {required: true})
    const token: string = core.getInput('token')

    if (!token) {
      core.info('无法获得 Token，跳过此次操作')
      return
    }
    // 初始化 GitHub 客户端
    const octokit = github.getOctokit(token)

    // 打印事件信息
    core.info(`event name: ${github.context.eventName}`)
    core.info(`action type: ${github.context.payload.action}`)

    // 处理 pull_request 事件
    if (
      github.context.eventName === 'pull_request' &&
      github.context.payload.action === 'closed'
    ) {
      // 只处理支持标签的拉取请求
      const issueType = checkLabel(github.context.payload.pull_request?.labels)
      if (issueType) {
        const ref: string = github.context.payload.pull_request?.head.ref
        const relatedIssueNumber = extractIssueNumberFromRef(ref)
        if (relatedIssueNumber) {
          await closeIssue(octokit, relatedIssueNumber)
          core.info(`议题 #${relatedIssueNumber} 已关闭`)
          try {
            await exec.exec('git', ['push', 'origin', '--delete', ref])
            core.info('已删除对应分支')
          } catch (error) {
            core.info('对应分支不存在或已删除')
          }
        }
        if (github.context.payload.pull_request?.merged) {
          core.info('发布的拉取请求已合并，准备更新拉取请求的提交')
          const pullRequests = await getPullRequests(octokit, issueType)
          resolveConflictPullRequests(octokit, pullRequests, base)
        } else {
          core.info('发布的拉取请求未合并，已跳过')
        }
      } else {
        core.info('拉取请求与插件无关，已跳过')
      }
      return
    }

    // 处理 push 事件
    if (github.context.eventName === 'push') {
      const publishType = checkCommitType(
        github.context.payload.head_commit.message
      )
      if (publishType) {
        core.info('发现提交为发布，准备更新拉取请求的提交')
        const pullRequests = await getPullRequests(octokit, publishType)
        resolveConflictPullRequests(octokit, pullRequests, base)
      } else {
        core.info('该提交不是发布，已跳过')
      }
      return
    }

    // 处理 issues 事件
    if (
      github.context.eventName === 'issues' &&
      github.context.payload.action &&
      ['opened', 'reopened', 'edited'].includes(github.context.payload.action)
    ) {
      // 从 GitHub Context 中获取议题的相关信息
      const issue_number = github.context.payload.issue?.number
      const issueBody = github.context.payload.issue?.body

      if (!issue_number || !issueBody) {
        core.setFailed('无法获取议题的信息')
        return
      }

      // 检查是否为指定类型的提交
      const publishType = checkTitle(github.context.payload.issue?.title)
      if (!publishType) {
        core.info('不是商店发布议题，已跳过')
        return
      }

      // 创建新分支
      // 命名示例 plugin/issue123
      const branchName = `plugin/issue${issue_number}`
      await exec.exec('git', ['checkout', '-b', branchName])

      // 插件作者信息
      const username = github.context.payload.issue?.user.login

      // 提取信息
      const info = extractInfo(publishType, issueBody, username)

      // 自动给议题添加标签
      await octokit.issues.addLabels({
        ...github.context.repo,
        issue_number,
        labels: [info.type]
      })

      // 更新文件并提交更改
      await updateFile(info)
      await commitandPush(branchName, info)

      // 创建拉取请求
      await createPullRequest(octokit, info, issue_number, branchName, base)
    } else {
      core.info('事件不是议题开启，重新开启或修改，已跳过')
    }
  } catch (error) {
    core.setFailed(error.message)
  }
}

run()
