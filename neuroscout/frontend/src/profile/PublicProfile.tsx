import * as React from 'react';

import { Avatar, Descriptions, Row, Spin } from 'antd';

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
}

interface PublicProfileState {
  profile: ApiUser;
  loaded: boolean;
  error: boolean;
}

class PublicProfile extends React.Component<PublicProfileProps, PublicProfileState> {
  constructor(props) {
    super(props);
    let profInit = profileInit();
    this.state = {
      profile: {
        ...profInit,
        analyses: [] as AppAnalysis[],
        predictor_collections: [] as PredictorCollection[],
        first_login: false
      },
      loaded: false,
      error: false
    };
  }

  componentDidMount() {
    if (this.state.loaded) {
      return;
    }
    api.getPublicProfile(this.props.id).then(response => {
      let newProfile = {...this.state.profile};
      let error = response.statusCode === 200;
      Object.keys(response).map(key => {
        if (newProfile.hasOwnProperty(key)) {
          newProfile[key] = response[key];
        }
      });
      this.setState({profile: newProfile, loaded: true, error: error});
    });
  }

  render() {
    let profile = this.state.profile;
    let descItems: any[] = [
      ['name', (<Descriptions.Item label="Name">{profile.name}</Descriptions.Item>)],
      ['institution', (<Descriptions.Item label="Institution">{profile.institution}</Descriptions.Item>)],
      ['orcid', (<Descriptions.Item label="ORCID iD">{profile.orcid}</Descriptions.Item>)],
      ['bio', (<Descriptions.Item label="Biography">{profile.bio}</Descriptions.Item>)],
      ['twitter_handle', (<Descriptions.Item label="Twitter">{profile.twitter_handle}</Descriptions.Item>)],
      ['personal_site', (<Descriptions.Item label="Personal Site">{profile.personal_site}</Descriptions.Item>)]
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
              <Avatar
                shape="circle"
                icon="user"
                src={profile.picture}
                className="headerAvatar"
              />
              <Descriptions column={1}>
                {descItems}
              </Descriptions>
              <br />
              <h3>Analyses by {profile.name}:</h3>
              <AnalysisListTable
                analyses={this.state.profile.analyses}
                datasets={this.props.datasets}
                cloneAnalysis={this.props.cloneAnalysis}
                publicList={true}
                loggedIn={this.props.loggedIn}
              />
            </>
          }
        </MainCol>
      </Row>
    );
  }
}

export default PublicProfile;
