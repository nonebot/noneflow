import * as core from '@actions/core'
import * as github from '@actions/github'
import * as exec from '@actions/exec'
import * as fs from 'fs'
import {GitHub} from '@actions/github/lib/utils'
import {IssuesGetResponseData, PullsListResponseData} from '@octokit/types'

/**插件所需要的信息 */
interface PluginInfo {
  /**import id */
  id: string
  /**pip地址 */
  link: string
  /**你的插件名称 */
  name: string
  /**简短描述插件功能 */
  desc: string
  /**开发者 */
  author: string
  /**插件项目仓库/主页链接 */
  repo: string
}

/**检查 Issue 是否带有 Plugin Label */
async function checkPluginLabel(
  octokit: InstanceType<typeof GitHub>,
  issueNumber: number
): Promise<boolean> {
  const response = await octokit.issues.get({
    owner: github.context.repo.owner,
    repo: github.context.repo.repo,
    issue_number: issueNumber
  })
  const title = response.data.title
  core.info(`Issue title: '${title}'`)
  const labels = response.data.labels
  return checkLabel(labels, 'Plugin')
}

/**检查 Labels 中是否具有某个名字 */
function checkLabel(
  labels: IssuesGetResponseData['labels'],
  name: string
): boolean {
  for (const label of labels) {
    if (label.name === name) {
      return true
    }
  }
  return false
}

/**从 Ref 中提取 Issue 编号 */
function extractIssueNumberFromRef(ref: string): number | undefined {
  const match = ref.match(/plugin\/issue(\d+)/)
  if (match) {
    return Number(match[1])
  }
}

/**更新 plugins.json
 * 并提交到 Git
 */
async function updatePluginsFileAndCommitPush(
  pluginInfo: PluginInfo,
  branchName: string
): Promise<void> {
  if (process.env.GITHUB_WORKSPACE) {
    const path: string = core.getInput('path', {required: true})
    const pluginJsonFilePath = `${process.env.GITHUB_WORKSPACE}/${path}`
    // 写入新数据
    fs.readFile(pluginJsonFilePath, 'utf8', (err, data) => {
      if (err) {
        core.setFailed(err)
      } else {
        const obj = JSON.parse(data)
        obj.push(pluginInfo)
        const json = JSON.stringify(obj, null, 2)
        fs.writeFile(pluginJsonFilePath, json, 'utf8', () => {})
      }
    })
    const commitMessage = `:beers: publish ${pluginInfo.name}`
    await exec.exec('git', [
      'config',
      '--global',
      'user.name',
      pluginInfo.author
    ])
    const useremail = `${pluginInfo.author}@users.noreply.github.com`
    await exec.exec('git', ['config', '--global', 'user.email', useremail])
    await exec.exec('git', ['add', '-A'])
    await exec.exec('git', ['commit', '-m', commitMessage])
    await exec.exec('git', ['push', 'origin', branchName, '-f'])
  }
}

/**从 Issue 内容提取插件信息 */
function extractPluginInfo(body: string, author: string): PluginInfo {
  const idRegexp = /\*\*插件 import 使用的名称\*\*[\n\r]+([^*\n\r]+)/
  const linkRegexp = /\*\*插件 install 使用的名称\*\*[\n\r]+([^*\n\r]+)/
  const descRegexp = /\*\*简短描述插件功能：\*\*[\n\r]+([^*\n\r]+)/
  const nameRegexp = /\*\*你的插件名称：\*\*[\n\r]+([^*\n\r]+)/
  const repoRegexp = /\*\*插件项目仓库\/主页链接\*\*[\n\r]+([^*\n\r]+)/

  const idMatch = body.match(idRegexp)
  const id = idMatch ? idMatch[1] : null
  const linkMatch = body.match(linkRegexp)
  const link = linkMatch ? linkMatch[1] : null
  const descMatch = body.match(descRegexp)
  const desc = descMatch ? descMatch[1] : null
  const nameMatch = body.match(nameRegexp)
  const name = nameMatch ? nameMatch[1] : null
  const repoMatch = body.match(repoRegexp)
  const repo = repoMatch ? repoMatch[1] : null

  if (id && link && desc && name && repo) {
    return {
      id,
      link,
      author,
      desc,
      name,
      repo
    }
  }
  throw new Error('无法匹配成功')
}

/**创建 Pull Request
 *
 * 同时添加 Plugin 标签
 */
async function createPullRequest(
  pluginInfo: PluginInfo,
  issueNumber: number,
  octokit: InstanceType<typeof GitHub>,
  branchName: string,
  base: string
): Promise<void> {
  const pullRequestTitle = `Plugin ${pluginInfo.name}`
  const pullRequestbody = `resolve #${issueNumber}`
  try {
    const pr = await octokit.pulls.create({
      owner: github.context.repo.owner,
      repo: github.context.repo.repo,
      title: pullRequestTitle,
      head: branchName,
      base,
      body: pullRequestbody
    })
    // 自动给 Pull Request 添加 Plugin 标签
    await octokit.issues.addLabels({
      owner: github.context.repo.owner,
      repo: github.context.repo.repo,
      issue_number: pr.data.number,
      labels: ['Plugin']
    })
  } catch (error) {
    if (error.message.includes(`A pull request already exists for`)) {
      core.info('该分支的拉取请求已创建，请前往查看')
    } else {
      throw error
    }
  }
}

/**获取所有带有 Plugin 标签的 Pull Request */
async function getAllPluginPullRequest(
  octokit: InstanceType<typeof GitHub>
): Promise<PullsListResponseData> {
  const listOfPulls = (
    await octokit.pulls.list({
      owner: github.context.repo.owner,
      repo: github.context.repo.repo,
      state: 'open'
    })
  ).data

  return listOfPulls.filter(pull => checkLabel(pull.labels, 'Plugin'))
}

/**根据关联的 Issue rebase 提交来解决冲突 */
async function rebaseAllOpenPullRequests(
  pullRequests: PullsListResponseData,
  base: string,
  octokit: InstanceType<typeof GitHub>
): Promise<void> {
  for (const pull of pullRequests) {
    // 切换到对应分支
    await exec.exec('git', ['checkout', '-b', pull.head.ref])
    // 重置之前的提交
    await exec.exec('git', ['reset', '--hard', base])
    const issue_number = extractIssueNumberFromRef(pull.head.ref)
    if (issue_number) {
      core.info(`正在处理 ${pull.title}`)
      const issue = await octokit.issues.get({
        ...github.context.repo,
        issue_number
      })
      const pluginInfo = extractPluginInfo(
        issue.data.body,
        issue.data.user.login
      )
      await updatePluginsFileAndCommitPush(pluginInfo, pull.head.ref)
      core.info(`拉取请求更新完毕`)
    } else {
      core.setFailed(`无法获取 ${pull.title} 对应的议题`)
    }
  }
}

/**关闭指定的议题 */
async function closeIssue(
  issue_number: number,
  octokit: InstanceType<typeof GitHub>
): Promise<void> {
  core.info(`正在关闭议题 #${issue_number}`)
  await octokit.issues.update({
    owner: github.context.repo.owner,
    repo: github.context.repo.repo,
    issue_number,
    state: 'closed'
  })
}

async function run(): Promise<void> {
  try {
    const token: string = core.getInput('token', {required: true})
    const base: string = core.getInput('base', {required: true})

    // 初始化 GitHub 客户端
    const octokit = github.getOctokit(token)

    // 打印事件信息
    core.info(`event name: ${github.context.eventName}`)
    core.info(`action type: ${github.context.payload.action}`)

    // 处理拉取请求的关闭事件
    if (github.context.eventName === 'pull_request') {
      if (github.context.payload.action === 'closed') {
        const ref: string = github.context.payload.pull_request?.head.ref
        const relatedIssueNumber = extractIssueNumberFromRef(ref)
        if (relatedIssueNumber) {
          await closeIssue(relatedIssueNumber, octokit)
          core.info(`议题 #${relatedIssueNumber}  已关闭`)
          await exec.exec('git', ['push', 'origin', '--delete', ref])
        }
      } else {
        core.info('不是拉取请求关闭事件，已跳过')
      }
      return
    }

    // 处理 push 事件
    if (github.context.eventName === 'push') {
      const commitMessage: string = github.context.payload.head_commit.message
      if (commitMessage.includes(':beers: publish')) {
        core.info('发现提交为插件发布，准备更新拉取请求的提交')
        const pullRequests = await getAllPluginPullRequest(octokit)
        rebaseAllOpenPullRequests(pullRequests, base, octokit)
      } else {
        core.info('该提交不是插件发布，已跳过')
      }
      return
    }

    // 从 GitHub Context 中获取议题的相关信息
    const issueNumber = github.context.payload.issue?.number
    const issueBody = github.context.payload.issue?.body

    if (!issueNumber || !issueBody) {
      core.setFailed('无法获取议题的信息')
      return
    }

    // 检查是否含有 Plugin 标签
    const isPluginIssue = await checkPluginLabel(octokit, issueNumber)

    if (!isPluginIssue) {
      core.info('没有 Plugin 标签，已跳过')
      return
    }

    // 插件作者信息
    const username = github.context.issue.owner

    // 创建新分支
    // plugin/issue123
    const branchName = `plugin/issue${issueNumber}`
    await exec.exec('git', ['checkout', '-b', branchName])

    // 更新 plugins.json 并提交更改
    const pluginInfo = extractPluginInfo(issueBody, username)
    await updatePluginsFileAndCommitPush(pluginInfo, branchName)

    // 提交 Pull Request
    // 标题里要注明 issue 编号
    await createPullRequest(pluginInfo, issueNumber, octokit, branchName, base)
  } catch (error) {
    core.setFailed(error.message)
  }
}

run()
