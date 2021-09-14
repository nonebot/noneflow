import * as github from '@actions/github'
import * as core from '@actions/core'
import * as exec from '@actions/exec'
import * as fs from 'fs'
import * as adapter from './types/adapter'
import * as bot from './types/bot'
import * as plugin from './types/plugin'
import {Info, PublishType} from './info'
import {
  IssuesGetResponseDataType,
  OctokitType,
  PullsListResponseDataType
} from './types/github'
import {commentTitle} from './constants'

/**检查标签是否含有指定类型
 *
 * 并返回指定的类型(Plugin Adapter Bot)
 *
 * 如果无返回则说明不含指定类型
 */
export function checkLabel(
  labels: IssuesGetResponseDataType['labels']
): PublishType | undefined {
  for (const label of labels) {
    if (
      typeof label !== 'string' &&
      ['Plugin', 'Adapter', 'Bot'].includes(label.name ?? 'None')
    ) {
      return label.name as PublishType
    }
  }
}

/**检查标题是否含有指定类型
 *
 * 并返回指定的类型(Plugin Adapter Bot)
 *
 * 如果无返回则说明不含指定类型
 */
export function checkTitle(title: string): PublishType | undefined {
  if (title.startsWith('Adapter:')) {
    return 'Adapter'
  }
  if (title.startsWith('Bot:')) {
    return 'Bot'
  }
  if (title.startsWith('Plugin:')) {
    return 'Plugin'
  }
}

/**检查提交信息是否含有指定类型
 *
 * 并返回指定的类型(Plugin Adapter Bot)
 *
 * 如果无返回则说明不含指定类型
 */
export function checkCommitType(
  commitMessage: string
): PublishType | undefined {
  if (commitMessage.startsWith(':beers: publish adapter')) {
    return 'Adapter'
  }
  if (commitMessage.startsWith(':beers: publish bot')) {
    return 'Bot'
  }
  if (commitMessage.startsWith(':beers: publish plguin')) {
    return 'Plugin'
  }
}

/**更新 json 文件 */
export async function updateFile(info: Info): Promise<void> {
  if (process.env.GITHUB_WORKSPACE) {
    let path: string
    // 去除 Info 中的 type
    let newInfo: {
      id?: string
      link?: string
      name: string
      desc: string
      author: string
      repo: string
    }
    switch (info.type) {
      case 'Adapter':
        path = core.getInput('adapter_path', {required: true})
        newInfo = {
          id: info.id,
          link: info.link,
          name: info.name,
          desc: info.desc,
          author: info.author,
          repo: info.repo
        }
        break
      case 'Bot':
        path = core.getInput('bot_path', {required: true})
        newInfo = {
          name: info.name,
          desc: info.desc,
          author: info.author,
          repo: info.repo
        }
        break
      case 'Plugin':
        path = core.getInput('plugin_path', {required: true})
        newInfo = {
          id: info.id,
          link: info.link,
          name: info.name,
          desc: info.desc,
          author: info.author,
          repo: info.repo
        }
        break
    }
    const jsonFilePath = `${process.env.GITHUB_WORKSPACE}/${path}`
    // 写入新数据
    fs.readFile(jsonFilePath, 'utf8', (err, data) => {
      if (err) {
        core.setFailed(err)
      } else {
        const obj = JSON.parse(data)
        obj.push(newInfo)
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
  info: Info
): Promise<void> {
  const commitMessage = `:beers: publish ${info.type.toLowerCase()} ${
    info.name
  }`
  await exec.exec('git', ['config', '--global', 'user.name', info.author])
  const useremail = `${info.author}@users.noreply.github.com`
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
  octokit: OctokitType,
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
  octokit: OctokitType,
  type: PublishType
): Promise<PullsListResponseDataType> {
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
export function extractIssueNumberFromRef(ref: string): number | undefined {
  const match = ref.match(/\/issue(\d+)/)
  if (match) {
    return Number(match[1])
  }
}

/**根据关联的议题提交来解决冲突
 *
 * 参考对应的议题重新更新对应分支
 */
export async function resolveConflictPullRequests(
  octokit: OctokitType,
  pullRequests: PullsListResponseDataType,
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

      const issueType = checkLabel(issue.data.labels)
      if (issueType) {
        const info = extractInfo(
          issueType,
          issue.data.body ?? '',
          issue.data.user?.login ?? ''
        )
        await updateFile(info)
        await commitandPush(pull.head.ref, info)
        core.info(`拉取请求更新完毕`)
      }
    } else {
      core.setFailed(`无法获取 ${pull.title} 对应的议题`)
    }
  }
}

/** 提取所需数据  */
export function extractInfo(
  publishType: PublishType,
  issueBody: string,
  username: string
): Info {
  let info: Info
  switch (publishType) {
    case 'Adapter':
      info = adapter.extractInfo(issueBody, username)
      break
    case 'Bot':
      info = bot.extractInfo(issueBody, username)
      break
    case 'Plugin':
      info = plugin.extractInfo(issueBody, username)
      break
  }
  return info
}

/**关闭指定的议题 */
export async function closeIssue(
  octokit: OctokitType,
  issue_number: number
): Promise<void> {
  core.info(`正在关闭议题 #${issue_number}`)
  await octokit.issues.update({
    ...github.context.repo,
    issue_number,
    state: 'closed'
  })
}

/**发布评论  */
export async function publishComment(
  octokit: OctokitType,
  issue_number: number,
  body: string
): Promise<void> {
  // 给评论添加统一的标题
  body = `${commentTitle}\n${body}`
  core.info('开始发布评论')
  if (!(await reuseComment(octokit, issue_number, body))) {
    await octokit.issues.createComment({
      ...github.context.repo,
      issue_number,
      body
    })
    core.info('评论创建完成')
  }
}
/**重复利用评论
 *
 * 如果发现之前评论过，直接修改之前的评论
 */
async function reuseComment(
  octokit: OctokitType,
  issue_number: number,
  body: string
): Promise<boolean> {
  const comments = await octokit.issues.listComments({
    ...github.context.repo,
    issue_number
  })
  if (comments) {
    // 检查相关评论是否拥有统一的标题
    const relatedComments = comments.data.filter(comment =>
      comment.body?.startsWith(commentTitle)
    )
    if (!relatedComments) {
      return false
    }
    const last_comment = relatedComments.pop()
    const comment_id = last_comment?.id
    if (comment_id) {
      core.info(`发现已有评论 ${last_comment?.id}，正在修改`)
      body += '\n\n:recycle: This comment has been updated with latest result.'
      octokit.issues.updateComment({
        ...github.context.repo,
        comment_id,
        body
      })
      return true
    }
  }
  return false
}
