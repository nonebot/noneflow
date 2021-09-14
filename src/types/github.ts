import * as github from '@actions/github'
import {GetResponseDataTypeFromEndpointMethod} from '@octokit/types'

const octokit = github.getOctokit('')

export type OctokitType = typeof octokit
export type PullsListResponseDataType = GetResponseDataTypeFromEndpointMethod<
  typeof octokit.pulls.list
>
export type IssuesGetResponseDataType = GetResponseDataTypeFromEndpointMethod<
  typeof octokit.issues.get
>
