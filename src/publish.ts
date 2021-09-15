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
  publishComment,
  resolveConflictPullRequests,
  updateFile
} from './utils'
import {OctokitType} from './types/github'
import {
  IssuesEvent,
  PullRequestEvent,
  PushEvent
} from '@octokit/webhooks-definitions/schema'
import {check, generateMessage} from './check'

/** 处理拉取请求 */
export async function processPullRequest(
  octokit: OctokitType,
  base: string
): Promise<void> {
  const pullRequestPayload = github.context.payload as PullRequestEvent

  // 因为合并拉取请求只会触发 closed 事件
  // 其他事件均对商店发布流程无影响
  if (pullRequestPayload.action !== 'closed') {
    core.info('事件不是关闭拉取请求，已跳过')
    return
  }

  // 只处理支持标签的拉取请求
  const issueType = checkLabel(pullRequestPayload.pull_request.labels)
  if (issueType) {
    const ref: string = pullRequestPayload.pull_request.head.ref
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
    if (pullRequestPayload.pull_request.merged) {
      core.info('发布的拉取请求已合并，准备更新拉取请求的提交')
      const pullRequests = await getPullRequests(octokit, issueType)
      resolveConflictPullRequests(octokit, pullRequests, base)
    } else {
      core.info('发布的拉取请求未合并，已跳过')
    }
  } else {
    core.info('拉取请求与发布无关，已跳过')
  }
}
/** 处理提交 */
export async function processPush(
  octokit: OctokitType,
  base: string
): Promise<void> {
  const pushPayload = github.context.payload as PushEvent

  if (!pushPayload.head_commit?.message) {
    core.setFailed('提交信息不存在')
    return
  }

  const publishType = checkCommitType(pushPayload.head_commit?.message)
  if (publishType) {
    core.info('发现提交为发布，准备更新拉取请求的提交')
    const pullRequests = await getPullRequests(octokit, publishType)
    resolveConflictPullRequests(octokit, pullRequests, base)
  } else {
    core.info('该提交不是发布，已跳过')
  }
}
/** 处理议题 */
export async function processIssues(
  octokit: OctokitType,
  base: string
): Promise<void> {
  const issuesPayload = github.context.payload as IssuesEvent

  if (['opened', 'reopened', 'edited'].includes(issuesPayload.action)) {
    // 从 GitHub Context 中获取议题的相关信息
    const issue_number = issuesPayload.issue.number
    const issueBody = issuesPayload.issue.body

    if (!issue_number || !issueBody) {
      core.setFailed('无法获取议题的信息')
      return
    }

    // 检查是否为指定类型的提交
    const publishType = checkTitle(issuesPayload.issue.title)
    if (!publishType) {
      core.info('不是商店发布议题，已跳过')
      return
    }

    // 插件作者信息
    const username = issuesPayload.issue.user.login

    // 提取信息
    const info = extractInfo(publishType, issueBody, username)

    // 自动给议题添加标签
    await octokit.issues.addLabels({
      ...github.context.repo,
      issue_number,
      labels: [info.type]
    })

    // 检查是否满足发布要求
    const checkStatus = await check(octokit, info)

    // 仅在通过检查的情况下创建拉取请求
    if (checkStatus.pass) {
      // 创建新分支
      // 命名示例 publish/issue123
      const branchName = `publish/issue${issue_number}`
      await exec.exec('git', ['checkout', '-b', branchName])

      // 更新文件并提交更改
      await updateFile(info)
      await commitandPush(branchName, info)

      // 创建拉取请求
      await createPullRequest(octokit, info, issue_number, branchName, base)
    } else {
      const message = generateMessage(checkStatus, info)
      await publishComment(octokit, issue_number, message)
      core.warning('发布没通过检查')
    }
  } else {
    core.info('事件不是议题开启，重新开启或修改，已跳过')
  }
}
