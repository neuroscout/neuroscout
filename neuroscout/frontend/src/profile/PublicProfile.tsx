import * as React from 'react';

import { Avatar, Card, Col, List, Row, Spin } from 'antd';
import { Link } from 'react-router-dom';

import { AnalysisListTable } from '../AnalysisList';
import { MainCol, Space } from '../HelperComponents';
import { profileEditItems, ApiUser, AppAnalysis, PredictorCollection, Dataset } from '../coretypes';
import { api } from '../api';
import { profileInit } from '../user';

interface PublicProfileProps {
  id: number;
  datasets: Dataset[];
  cloneAnalysis: (id: string) => void;
  loggedIn: boolean;
  isUser: boolean;
}

interface PublicProfileState {
  profile: ApiUser;
  loaded: boolean;
  error: boolean;
  analysesLoaded: boolean;
  analyses: AppAnalysis[];
}

class PublicProfile extends React.Component<PublicProfileProps, PublicProfileState> {
  constructor(props) {
    super(props);
    let profInit = profileInit();
    this.state = {
      profile: {
        ...profInit,
        predictor_collections: [] as PredictorCollection[],
        first_login: false
      },
      analysesLoaded: false,
      analyses: [] as AppAnalysis[],
      loaded: false,
      error: false
    };
  }

  componentDidMount() {
    if (this.state.loaded) {
      return;
    }
    api.getPublicProfile(this.props.id)
      .then(response => {
        let newProfile = {...this.state.profile};
        let error = response.statusCode === 200;
        Object.keys(response).map(key => {
          if (newProfile.hasOwnProperty(key)) {
            newProfile[key] = response[key];
          }
        });
        this.setState({profile: newProfile, loaded: true, error: error});
      });
    let id = !this.props.isUser ? this.props.id : undefined;
    api.getAnalyses(id).then(analyses => this.setState({analyses: analyses, analysesLoaded: true}));
  }

  render() {
    let profile = this.state.profile;
    let descItems: any[] = [
      ['institution', {title: 'Institution', desc: profile.institution}],
      ['orcid', {title: 'ORCID iD', desc: profile.orcid}],
      ['bio', {title: 'Biography', desc: profile.bio}],
      ['twitter_handle', {title: 'Twitter', desc: profile.twitter_handle}],
      ['personal_site', {title: 'Personal Site', desc: profile.personal_site}]
    ];
    descItems = descItems.filter(x => !!profile[x[0]]).map(x => x[1]);

    return (
      <Row type="flex" justify="center" style={{ background: '#fff', padding: 0 }}>
        <MainCol>
          {!this.state.loaded &&
            <Spin spinning={!this.state.loaded} />
          }
          {this.state.loaded &&
            <>
              <div className="profileHeader">
                <Avatar
                  shape="circle"
                  icon="user"
                  src={profile.picture}
                />
                <Space />
                <span className="profileName">
                  {profile.name}
                </span>
              </div>
              <br />
              <Col lg={{ span: 6 }}>
              {editProfileList(this.props.isUser)}
              {descItems.length > 0 &&
                <List
                  dataSource={descItems}
                  itemLayout="vertical"
                  renderItem={item => (
                    <List.Item>
                      {item.title}: {item.desc}
                    </List.Item>
                  )}
                />
              }
              </Col>
              <Col lg={{ span: 18 }}>
              <AnalysisListTable
                analyses={this.state.analyses}
                datasets={this.props.datasets}
                cloneAnalysis={this.props.cloneAnalysis}
                publicList={true}
                loggedIn={this.props.loggedIn}
                loading={!this.state.analysesLoaded}
              />
              </Col>
            </>
          }
        </MainCol>
      </Row>
    );
  }
}

function editProfileList(isUser: Boolean) {
  if (isUser) {
    return <Link to="/profile/edit">Edit Profile</Link>;
  }
  return '';
}

export default PublicProfile;
