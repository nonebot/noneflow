import * as core from '@actions/core'
import * as github from '@actions/github'
import * as exec from '@actions/exec'
import * as io from '@actions/io'
import {GitHub} from '@actions/github/lib/utils'

async function run(): Promise<void> {
  try {
    const token: string = core.getInput('token', {required: true})

    // 从 GitHub context 中获取 issue 的相关信息
    const issueNumber = github.context.payload.issue?.number
    const issueBody = github.context.payload.issue?.body

    if (!issueNumber || !issueBody) {
      core.setFailed('无法获取 issue 的信息')
      return
    }
    // GitHub 客户端
    const octokit = github.getOctokit(token)

    if (await checkPluginLabel(octokit, issueNumber)) {
      const git = await GitCommandManager.create()
      // 创建新分支
      await creatBranch(git, github.context.actor)
      // 更新 plugins.json

      // 提交 PR
      // octokit.pulls.create()
    }
  } catch (error) {
    core.setFailed(error.message)
  }
}

// 检查 issue 是否带有 Plugin label
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
  return title.search('plugin') !== -1
}

class GitCommandManager {
  private gitPath: string
  private workingDirectory: string

  private constructor(workingDirectory: string, gitPath: string) {
    this.workingDirectory = workingDirectory
    this.gitPath = gitPath
  }

  static async create(): Promise<GitCommandManager> {
    const gitPath = await io.which('git', true)
    const workingDirectory = process.env['GITHUB_WORKSPACE']
    if (!workingDirectory) {
      throw new Error('GITHUB_WORKSPACE not defined')
    }
    core.info(`workingDirectory: '${workingDirectory}'`)
    return new GitCommandManager(workingDirectory, gitPath)
  }

  async checkout(name: string): Promise<void> {
    const args = ['checkout', '-b', name]
    await this.exec(args)
  }

  async exec(args: string[]): Promise<void> {
    const options = {
      cwd: this.workingDirectory
    }

    await exec.exec(`"${this.gitPath}"`, args, options)
  }
}

// 创建新分支
async function creatBranch(
  git: GitCommandManager,
  name: string
): Promise<void> {
  await exec.exec('git', ['checkout', '-b', name])
}

interface Plugin {
  id: string
  link: string
  name: string
  desc: string
  author: string
  repo: string
}

async function updatePlugins(plugin: Plugin): Promise<void> {}

run()
