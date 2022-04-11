import * as React from 'react'
import memoize from 'memoize-one'

import { UserOutlined } from '@ant-design/icons'

import { Avatar, Card, Col, List, Row, Spin } from 'antd'
import { Link, withRouter } from 'react-router-dom'
import { RouteComponentProps } from 'react-router'

import { AnalysisListTable } from '../browser/AnalysisList'
import { MainCol, Space, NotFound } from '../HelperComponents'
import {
  profileEditItems,
  ApiUser,
  AppAnalysis,
  PredictorCollection,
  Dataset,
} from '../coretypes'
import { api } from '../api'
import { profileInit } from '../user'

interface PublicProfileProps {
  user_name: string
  datasets: Dataset[]
  cloneAnalysis: (id: string) => Promise<string>
  loggedIn: boolean
  isUser: boolean
}

interface PublicProfileState {
  profile: ApiUser
  loaded: boolean
  error: number
  analysesLoaded: boolean
  analyses: AppAnalysis[]
}

class PublicProfile extends React.Component<
  PublicProfileProps & RouteComponentProps,
  PublicProfileState
> {
  constructor(props) {
    super(props)
    const profInit = profileInit()
    this.state = {
      profile: {
        ...profInit,
        predictor_collections: [] as PredictorCollection[],
        first_login: false,
      },
      analysesLoaded: false,
      analyses: [] as AppAnalysis[],
      loaded: false,
      error: 0,
    }
  }

  memoizeId = memoize(user_name => {
    void api.getPublicProfile(user_name).then(response => {
      const newProfile = { ...this.state.profile }
      const error = response.statusCode
      Object.keys(response).map(key => {
        if (newProfile.hasOwnProperty(key)) {
          newProfile[key] = response[key]
        }
      })
      this.setState({ profile: newProfile, loaded: true, error: error })
    })
    void api
      .getAnalyses(this.props.user_name)
      .then(analyses =>
        this.setState({ analyses: analyses, analysesLoaded: true }),
      )
  })

  render() {
    this.memoizeId(this.props.user_name)
    if (this.state.error === 404) {
      return <NotFound />
    }
    const profile = this.state.profile
    let descItems: any[] = [
      ['institution', { title: 'Institution', desc: profile.institution }],
      ['orcid', { title: 'ORCID iD', desc: profile.orcid }],
      ['bio', { title: 'Biography', desc: profile.bio }],
      [
        'twitter_handle',
        {
          title: 'Twitter',
          desc: (
            <a
              target="_blank"
              href={'https://twitter.com/' + profile.twitter_handle}
              rel="noreferrer"
            >
              {'@' + profile.twitter_handle}
            </a>
          ),
        },
      ],
      [
        'personal_site',
        {
          title: 'Personal Site',
          desc: (
            <a
              target="_blank"
              href={'https://' + profile.personal_site}
              rel="noreferrer"
            >
              {profile.personal_site}
            </a>
          ),
        },
      ],
    ]
    descItems = descItems.filter(x => !!profile[x[0]]).map(x => x[1])
    if (profile.public_email) {
      descItems = [{ title: 'Email', desc: profile.email }, ...descItems]
    }

    return (
      <Row justify="center" style={{ background: '#fff', padding: 0 }}>
        <MainCol>
          {!this.state.loaded && <Spin spinning={!this.state.loaded} />}
          {this.state.loaded && (
            <>
              <div className="profileHeader">
                <Avatar
                  shape="circle"
                  icon={<UserOutlined />}
                  src={profile.picture}
                />
                <Space />
                <span className="profileName">{profile.name}</span>
              </div>
              <br />
              <Col lg={{ span: 6 }}>
                {editProfileList(this.props.isUser)}
                {descItems.length > 0 && (
                  <List
                    dataSource={descItems}
                    itemLayout="vertical"
                    renderItem={item => (
                      <List.Item>
                        {item.title}: {item.desc}
                      </List.Item>
                    )}
                  />
                )}
              </Col>
              <Col lg={{ span: 18 }}>
                <AnalysisListTable
                  analyses={this.state.analyses}
                  datasets={this.props.datasets}
                  cloneAnalysis={this.props.cloneAnalysis}
                  publicList
                  loggedIn={this.props.loggedIn}
                  loading={!this.state.analysesLoaded}
                />
              </Col>
            </>
          )}
        </MainCol>
      </Row>
    )
  }
}

function editProfileList(isUser: boolean) {
  if (isUser) {
    return <Link to="/profile/edit">Edit Profile</Link>
  }
  return ''
}

export default withRouter(PublicProfile)
