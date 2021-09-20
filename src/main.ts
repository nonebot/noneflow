import * as core from '@actions/core'
import * as github from '@actions/github'
import {processIssues, processPullRequest, processPush} from './publish'

async function run(): Promise<void> {
  try {
    const base: string = core.getInput('base', {required: true})
    const token: string = core.getInput('token')

    if (!token) {
      core.warning('无法获得 Token，跳过此次操作')
      return
    }
    // 初始化 GitHub 客户端
    const octokit = github.getOctokit(token)

    // 打印事件信息
    core.info(`event name: ${github.context.eventName}`)
    core.info(`action type: ${github.context.payload.action}`)

    if (github.context.eventName === 'pull_request') {
      // 处理 pull_request 事件
      await processPullRequest(octokit, base)
      return
    }

    // 处理 push 事件
    if (github.context.eventName === 'push') {
      await processPush(octokit, base)
      return
    }

    // 处理 issues 事件
    if (github.context.eventName === 'issues') {
      await processIssues(octokit, base)
      return
    }
  } catch (error) {
    core.setFailed(error.message)
  }
}

run()
