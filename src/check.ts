import {OctokitType} from './types/github'
import {PluginInfo} from './types/plugin'
import {AdapterInfo} from './types/adapter'
import {HttpClient} from '@actions/http-client'
import {Info} from './types/info'
import {BotInfo} from './types/bot'

interface CheckStatus {
  /**是否能访问项目仓库/主页 */
  repo: boolean
  /**是否发布 */
  published: boolean
  /**是否满足要求 */
  pass: boolean
}

export async function check(
  octokit: OctokitType,
  info: Info
): Promise<CheckStatus> {
  let status: CheckStatus
  // 不同类型有不同类型的检查方法
  switch (info.type) {
    case 'Bot':
      status = await checkBot(octokit, info)
      break
    case 'Adapter':
      status = await checkAdapter(octokit, info)
      break
    case 'Plugin':
      status = await checkPlugin(octokit, info)
      break
  }
  return status
}

async function checkPlugin(
  octokit: OctokitType,
  info: PluginInfo
): Promise<CheckStatus> {
  const published = await checkPyPI(info.link)
  const repo = await checkRepo(info.repo)

  return {
    repo,
    published,
    pass: published && repo
  }
}

async function checkBot(
  octokit: OctokitType,
  info: BotInfo
): Promise<CheckStatus> {
  const repo = await checkRepo(info.repo)

  return {
    repo,
    published: true,
    pass: repo
  }
}

async function checkAdapter(
  octokit: OctokitType,
  info: AdapterInfo
): Promise<CheckStatus> {
  const published = await checkPyPI(info.link)
  const repo = await checkRepo(info.repo)

  return {
    repo,
    published,
    pass: published && repo
  }
}

async function checkPyPI(id: string): Promise<boolean> {
  const url = `https://pypi.org/pypi/${id}/json`
  return await checkUrl(url)
}

async function checkRepo(repo: string): Promise<boolean> {
  const url = getRepoUrl(repo)
  return await checkUrl(url)
}

function getRepoUrl(repo: string): string {
  if (repo.startsWith('http://') || repo.startsWith('https://')) {
    return repo
  } else {
    return `https://github.com/${repo}`
  }
}

/**
 * 检查 URL 是否可以访问
 *
 * @param url 需要检查的网址
 * @returns
 */
async function checkUrl(url: string): Promise<boolean> {
  const http = new HttpClient()
  try {
    const res = await http.get(url)
    if (res.message.statusCode === 200) {
      return true
    }
    return false
  } catch {
    return false
  }
}

export function generateMessage(status: CheckStatus, info: Info): string {
  let message = `> ${info.type}: ${info.name}`

  if (status.pass) {
    message += '\n\n**✅ All tests passed, you are ready to go!**'
  } else {
    message +=
      '\n\n**⚠️ We have found following problem(s) in pre-publish progress:**'
  }

  const errorMessage: string[] = []
  if (!status.repo) {
    errorMessage.push(
      `<li>⚠️ Project <a href="${getRepoUrl(
        info.repo
      )}">homepage</a> returns 404.<dt>  Please make sure that your project has a publicly visible homepage.</dt></li>`
    )
  }
  if (info.type === 'Adapter' || info.type === 'Plugin') {
    if (!status.published) {
      errorMessage.push(
        `<li>⚠️ Package <a href="https://pypi.org/project/${info.link}/">${info.link}</a> is not available on PyPI.<dt>  Please publish your package to PyPI.</dt></li>`
      )
    }
  }

  if (errorMessage.length !== 0) {
    message += `\n<pre><code>${errorMessage.join('\n')}</code></pre>`
  }

  const detailMessage: string[] = []
  if (status.repo) {
    detailMessage.push(
      `<li>✅ Project <a href="${getRepoUrl(
        info.repo
      )}">homepage</a> returns 200.</li>`
    )
  }
  if (info.type === 'Adapter' || info.type === 'Plugin') {
    if (status.published) {
      detailMessage.push(
        `<li>✅ Package <a href="https://pypi.org/project/${info.link}/">${info.link}</a> is available on PyPI.</li>`
      )
    }
  }

  if (detailMessage.length !== 0) {
    message += `\n<details>
    <summary>Report Detail</summary>
    <pre><code>${detailMessage.join('\n')}</code></pre>
    </details>`
  }

  return message
}
