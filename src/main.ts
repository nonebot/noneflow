import * as core from '@actions/core'
import * as github from '@actions/github'
import * as exec from '@actions/exec'
import * as fs from 'fs'
import {GitHub} from '@actions/github/lib/utils'
import {IssuesGetResponseData, PullsListResponseData} from '@octokit/types'
import {PluginInfo, extractPluginInfo} from './plugin'

/**检查是否含有插件标签 */
function checkPluginLabel(labels: IssuesGetResponseData['labels']): boolean {
  for (const label of labels) {
    if (label.name === 'Plugin') {
      return true
    }
  }
  return false
}

/**从 Ref 中提取标签编号 */
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
        fs.writeFile(pluginJsonFilePath, json, 'utf8', () => {
          core.info(`${pluginJsonFilePath} 更新完成`)
        })
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

/**创建拉取请求
 *
 * 同时添加 Plugin 标签
 * 内容关联上对应的议题
 */
async function createPullRequest(
  octokit: InstanceType<typeof GitHub>,
  pluginInfo: PluginInfo,
  issueNumber: number,
  branchName: string,
  base: string
): Promise<void> {
  const pullRequestTitle = `Plugin: ${pluginInfo.name}`
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
    // 自动给拉取请求添加 Plugin 标签
    await octokit.issues.addLabels({
      ...github.context.repo,
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

/**获取所有带有 Plugin 标签的拉取请求 */
async function getAllPluginPullRequest(
  octokit: InstanceType<typeof GitHub>
): Promise<PullsListResponseData> {
  const pulls = (
    await octokit.pulls.list({
      ...github.context.repo,
      state: 'open'
    })
  ).data

  return pulls.filter(pull => checkPluginLabel(pull.labels))
}

/**根据关联的议题提交来解决冲突
 *
 * 参考对应的议题重新更新对应分支
 */
async function resolveConflictPullRequests(
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
          const pullRequests = await getAllPluginPullRequest(octokit)
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
        const pullRequests = await getAllPluginPullRequest(octokit)
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
      await updatePluginsFileAndCommitPush(pluginInfo, branchName)

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
