import * as core from '@actions/core'
import * as github from '@actions/github'
import * as exec from '@actions/exec'
import * as fs from 'fs'
import {GitHub} from '@actions/github/lib/utils'

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
  for (const label of labels) {
    if (label.name === 'Plugin') {
      return true
    }
  }
  return false
}

/**更新 plugins.json */
async function updatePluginsFile(pluginInfo: PluginInfo): Promise<void> {
  if (process.env.GITHUB_WORKSPACE) {
    const pluginJsonFilePath = `${process.env.GITHUB_WORKSPACE}/docs/.vuepress/public/plugins.json`
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
  }
}

/**从 Issue 内容提取插件信息 */
function extractPluginInfo(body: string): PluginInfo {
  const match = body.match(
    /\*\*你的插件名称：\*\*[\n\r]+(?<name>.*)[\n\r]+\*\*简短描述插件功能：\*\*[\n\r]+(?<desc>.*)[\n\r]+\*\*插件 import 使用的名称\*\*[\n\r]+(?<id>.*)[\n\r]+\*\*插件 install 使用的名称\*\*[\n\r]+(?<link>.*)[\n\r]+\*\*插件项目仓库\/主页链接\*\*[\n\r]+(?<repo>.*)/
  )
  if (match?.groups) {
    return {
      id: match.groups.id,
      link: match.groups.link,
      author: 'test',
      desc: match.groups.desc,
      name: match.groups.name,
      repo: match.groups.repo
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
  branchName: string
): Promise<void> {
  const pullRequestTitle = `Plugin ${pluginInfo.name} (resolve #${issueNumber})`
  const pr = await octokit.pulls.create({
    owner: github.context.repo.owner,
    repo: github.context.repo.repo,
    title: pullRequestTitle,
    head: branchName,
    base: 'main',
    body: pullRequestTitle
  })
  // 自动给 Pull Request 添加 Plugin 标签
  await octokit.issues.addLabels({
    owner: github.context.repo.owner,
    repo: github.context.repo.repo,
    issue_number: pr.data.number,
    labels: ['Plugin']
  })
}

async function run(): Promise<void> {
  try {
    const token: string = core.getInput('token', {required: true})

    // 从 GitHub Context 中获取 Issue 的相关信息
    const issueNumber = github.context.payload.issue?.number
    const issueBody = github.context.payload.issue?.body

    if (!issueNumber || !issueBody) {
      core.setFailed('无法获取 issue 的信息')
      return
    }
    // 初始化 GitHub 客户端
    const octokit = github.getOctokit(token)

    // 检查是否含有 Plugin 标签
    const isPluginIssue = await checkPluginLabel(octokit, issueNumber)

    if (!isPluginIssue) {
      core.info('没有 Plugin 标签，不处理')
      return
    }

    // 创建新分支
    // plugin/issue123
    const branchName = `plugin/issue${issueNumber}`
    await exec.exec('git', ['checkout', '-b', branchName])

    // 更新 plugins.json
    const pluginInfo = extractPluginInfo(issueBody)
    pluginInfo.author = github.context.issue.owner
    await updatePluginsFile(pluginInfo)

    // 提交修改
    const commitMessage = `:beers: publish ${pluginInfo.name}`
    const username = github.context.issue.owner
    core.info(`username: ${username}`)
    const user = await octokit.users.getByUsername({username})
    const useremail = user.data.email ?? 'bot@github.com'
    await exec.exec('git', ['config', '--global', 'user.name', username])
    await exec.exec('git', ['config', '--global', 'user.email', useremail])
    await exec.exec('git', ['add', '-A'])
    await exec.exec('git', ['commit', '-m', commitMessage])
    await exec.exec('git', ['push', 'origin', branchName, '-f'])

    // 提交 Pull Request
    // 标题里要注明 issue 编号
    await createPullRequest(pluginInfo, issueNumber, octokit, branchName)
  } catch (error) {
    core.setFailed(error.message)
  }
}

run()
