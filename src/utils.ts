import * as github from '@actions/github'
import * as core from '@actions/core'
import * as exec from '@actions/exec'
import * as fs from 'fs'
import {IssuesGetResponseData} from '@octokit/types'
import {Info, IssueType} from './info'
import {GitHub} from '@actions/github/lib/utils'
import {PullsListResponseData} from '@octokit/types'
import * as adapter from './types/adapter'
import * as bot from './types/bot'
import * as plugin from './types/plugin'

/**检查是否含有指定标签
 *
 * Plugin Adapter Bot
 */
export function checkLabel(
  labels: IssuesGetResponseData['labels']
): IssueType | undefined {
  for (const label of labels) {
    if (['Plugin', 'Adapter', 'Bot'].includes(label.name)) {
      return label.name as IssueType
    }
  }
}

/**更新 json 文件 */
async function updateFile(info: Info): Promise<void> {
  if (process.env.GITHUB_WORKSPACE) {
    let path: string
    switch (info.type) {
      case 'Adapter':
        path = core.getInput('adapter_path', {required: true})
      case 'Bot':
        path = core.getInput('bot_path', {required: true})
      case 'Plugin':
        path = core.getInput('plugin_path', {required: true})
    }
    const jsonFilePath = `${process.env.GITHUB_WORKSPACE}/${path}`
    // 写入新数据
    fs.readFile(jsonFilePath, 'utf8', (err, data) => {
      if (err) {
        core.setFailed(err)
      } else {
        const obj = JSON.parse(data)
        obj.push(info)
        const json = JSON.stringify(obj, null, 2)
        fs.writeFile(jsonFilePath, json, 'utf8', () => {
          core.info(`${jsonFilePath} 更新完成`)
        })
      }
    })
  } else {
    core.setFailed('GITHUB_WORKSPACE 为空，无法确定文件位置')
  }
}

/**提交到 Git*/
export async function commitandPush(
  branchName: string,
  username: string,
  commitMessage: string
): Promise<void> {
  await exec.exec('git', ['config', '--global', 'user.name', username])
  const useremail = `${username}@users.noreply.github.com`
  await exec.exec('git', ['config', '--global', 'user.email', useremail])
  await exec.exec('git', ['add', '-A'])
  await exec.exec('git', ['commit', '-m', commitMessage])
  await exec.exec('git', ['push', 'origin', branchName, '-f'])
}

/**创建拉取请求
 *
 * 同时添加对应标签
 * 内容关联上对应的议题
 */
export async function createPullRequest(
  octokit: InstanceType<typeof GitHub>,
  info: Info,
  issueNumber: number,
  branchName: string,
  base: string
): Promise<void> {
  const pullRequestTitle = `${info.type}: ${info.name}`
  // 关联相关议题，当拉取请求合并时会自动关闭对应议题
  const pullRequestbody = `resolve #${issueNumber}`
  try {
    // 创建拉取请求
    const pr = await octokit.pulls.create({
      ...github.context.repo,
      title: pullRequestTitle,
      head: branchName,
      base,
      body: pullRequestbody
    })
    // 自动给拉取请求添加标签
    await octokit.issues.addLabels({
      ...github.context.repo,
      issue_number: pr.data.number,
      labels: [info.type]
    })
  } catch (error) {
    if (error.message.includes(`A pull request already exists for`)) {
      core.info('该分支的拉取请求已创建，请前往查看')
    } else {
      throw error
    }
  }
}

/**获取所有带有指定标签的拉取请求
 *
 * 只支持 Plugin, Adapter, Bot
 */
export async function getPullRequests(
  octokit: InstanceType<typeof GitHub>,
  type: IssueType
): Promise<PullsListResponseData> {
  const pulls = (
    await octokit.pulls.list({
      ...github.context.repo,
      state: 'open'
    })
  ).data

  return pulls.filter(pull => {
    return checkLabel(pull.labels) === type
  })
}

/**从 Ref 中提取标签编号 */
function extractIssueNumberFromRef(ref: string): number | undefined {
  const match = ref.match(/plugin\/issue(\d+)/)
  if (match) {
    return Number(match[1])
  }
}

/**根据关联的议题提交来解决冲突
 *
 * 参考对应的议题重新更新对应分支
 */
export async function resolveConflictPullRequests(
  octokit: InstanceType<typeof GitHub>,
  pullRequests: PullsListResponseData,
  base: string
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

      let info: Info
      const issueType = checkLabel(issue.data.labels)
      if (issueType) {
        switch (issueType) {
          case 'Adapter':
            info = adapter.extractInfo(issue.data.body, issue.data.user.login)
          case 'Bot':
            info = bot.extractInfo(issue.data.body, issue.data.user.login)
          case 'Plugin':
            info = plugin.extractInfo(issue.data.body, issue.data.user.login)
        }
        await updateFile(info)
        const commitMessage = `:beers: publish ${info.type.toLowerCase} ${info.name}`
        await commitandPush(pull.head.ref, info.author, commitMessage)
        core.info(`拉取请求更新完毕`)
      }
    } else {
      core.setFailed(`无法获取 ${pull.title} 对应的议题`)
    }
  }
}

/**关闭指定的议题 */
export async function closeIssue(
  octokit: InstanceType<typeof GitHub>,
  issue_number: number
): Promise<void> {
  core.info(`正在关闭议题 #${issue_number}`)
  await octokit.issues.update({
    ...github.context.repo,
    issue_number,
    state: 'closed'
  })
}
