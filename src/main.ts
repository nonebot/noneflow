import * as core from '@actions/core'
import * as github from '@actions/github'
import * as exec from '@actions/exec'

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
      // 只处理标签是 Plugin 的拉取请求
      if (checkPluginLabel(github.context.payload.pull_request?.labels)) {
        const ref: string = github.context.payload.pull_request?.head.ref
        const relatedIssueNumber = extractIssueNumberFromRef(ref)
        if (relatedIssueNumber) {
          await closeIssue(octokit, relatedIssueNumber)
          core.info(`议题 #${relatedIssueNumber}  已关闭`)
          try {
            await exec.exec('git', ['push', 'origin', '--delete', ref])
            core.info('已删除对应分支')
          } catch (error) {
            core.info('对应分支不存在或已删除')
          }
        }
        if (github.context.payload.pull_request?.merged) {
          core.info('发布插件的拉取请求已合并，准备更新拉取请求的提交')
          const pullRequests = await getPullRequests(octokit, 'plugin')
          resolveConflictPullRequests(octokit, pullRequests, base)
        } else {
          core.info('发布插件的拉取请求未合并，已跳过')
        }
      } else {
        core.info('拉取请求与插件无关，已跳过')
      }
      return
    }

    // 处理 push 事件
    if (github.context.eventName === 'push') {
      const commitMessage: string = github.context.payload.head_commit.message
      if (commitMessage.includes(':beers: publish')) {
        core.info('发现提交为插件发布，准备更新拉取请求的提交')
        const pullRequests = await getPullRequests(octokit, 'plugin')
        resolveConflictPullRequests(octokit, pullRequests, base)
      } else {
        core.info('该提交不是插件发布，已跳过')
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
      const issueNumber = github.context.payload.issue?.number
      const issueBody = github.context.payload.issue?.body

      if (!issueNumber || !issueBody) {
        core.setFailed('无法获取议题的信息')
        return
      }

      // 检查是否含有 Plugin 标签
      const isPluginIssue = checkPluginLabel(
        github.context.payload.issue?.labels
      )
      if (!isPluginIssue) {
        core.info('没有 Plugin 标签，已跳过')
        return
      }

      // 创建新分支
      // 命名示例 plugin/issue123
      const branchName = `plugin/issue${issueNumber}`
      await exec.exec('git', ['checkout', '-b', branchName])

      // 插件作者信息
      const username = github.context.payload.issue?.user.login

      // 更新 plugins.json 并提交更改
      const pluginInfo = extractPluginInfo(issueBody, username)
      await updateFileAndCommitPush(branchName)

      // 创建拉取请求
      await createPullRequest(
        octokit,
        pluginInfo,
        issueNumber,
        branchName,
        base
      )
    } else {
      core.info('事件不是议题开启，重新开启或修改，已跳过')
    }
  } catch (error) {
    core.setFailed(error.message)
  }
}

run()
