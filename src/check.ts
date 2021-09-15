import * as core from '@actions/core'
import * as github from '@actions/github'
import {
  checkTitle,
  extractInfo,
  extractIssueNumberFromRef,
  publishComment
} from './utils'
import {OctokitType} from './types/github'
import {PluginInfo} from './types/plugin'
import {AdapterInfo} from './types/adapter'
import {PullRequestEvent} from '@octokit/webhooks-definitions/schema'
import {HttpClient} from '@actions/http-client'
import {Info} from './types/info'

interface CheckStatus {
  /**是否发布 */
  published: boolean
  /**是否满足要求 */
  pass: boolean
}

export async function check(octokit: OctokitType): Promise<void> {
  const pullRequestPayload = github.context.payload as PullRequestEvent

  // 检查是否为指定类型的提交
  // 通过标题来判断，因为创建拉取请求时并没有标签
  const publishType = checkTitle(pullRequestPayload.pull_request.title)
  if (publishType) {
    const ref: string = pullRequestPayload.pull_request.head.ref
    const issue_number = extractIssueNumberFromRef(ref)
    if (!issue_number) {
      core.setFailed('无法获取议题')
      return
    }
    const issue = await octokit.issues.get({
      ...github.context.repo,
      issue_number
    })
    const info = extractInfo(
      publishType,
      issue.data.body ?? '',
      issue.data.user?.login ?? ''
    )
    let status: CheckStatus
    // 不同类型有不同类型的检查方法
    switch (info.type) {
      case 'Bot':
        // status = await checkBot(octokit, info)
        status = {
          published: true,
          pass: true
        }
        break
      case 'Adapter':
        status = await checkAdapter(octokit, info)
        break
      case 'Plugin':
        status = await checkPlugin(octokit, info)
        break
    }
    const message = generateMessage(status, info)
    await publishComment(octokit, pullRequestPayload.number, message)
    if (!status.pass) {
      core.setFailed('发布没通过检查')
    }
  } else {
    core.info('拉取请求与发布无关，已跳过')
  }
}

async function checkPlugin(
  octokit: OctokitType,
  info: PluginInfo
): Promise<CheckStatus> {
  const onPyPI = await checkPyPI(info.link)

  return {
    published: onPyPI,
    pass: onPyPI
  }
}

// async function checkBot(
//   octokit: OctokitType,
//   info: BotInfo
// ): Promise<CheckStatus> {
//   return {
//     published: true,
//     pass: true
//   }
// }

async function checkAdapter(
  octokit: OctokitType,
  info: AdapterInfo
): Promise<CheckStatus> {
  const onPyPI = await checkPyPI(info.link)

  return {
    published: onPyPI,
    pass: onPyPI
  }
}

async function checkPyPI(id: string): Promise<boolean> {
  const url = `https://pypi.org/pypi/${id}/json`
  const http = new HttpClient()
  const res = await http.get(url)
  if (res.message.statusCode === 200) {
    return true
  }
  return false
}

function generateMessage(status: CheckStatus, info: Info): string {
  let message = `${info.type}: ${info.name}`

  if (info.type === 'Bot') {
    message += 'Everything is ready to go'
  } else if (status.pass) {
    message += `\n\nPackage is available on PyPI([${info.link}](https://pypi.org/project/${info.link}/))`
    message += `\nEverything is ready to go`
  } else {
    message += `\n\nPackage is not available on PyPI([${info.link}](https://pypi.org/project/${info.link}/))`
    message += `\nPlease publish to PyPI`
  }

  return message
}
