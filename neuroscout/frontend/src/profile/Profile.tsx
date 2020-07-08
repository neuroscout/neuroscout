import * as React from 'react';
import { Divider, Row, Col, Button, Card, Form, Input, Switch } from 'antd';
import { MainCol } from '../HelperComponents';

import memoize from 'memoize-one';

import { AuthStoreState, profileEditItems, ProfileState } from '../coretypes';
import { api } from '../api';
import { Space } from '../HelperComponents';

/*
  jwt: string;
  loggedIn: boolean;
  openLogin: boolean;
  openSignup: boolean;
  openReset: boolean;
  openEnterResetToken: boolean;
  openTour: boolean;
  loginError: string;
  signupError: string;
  resetError: string;
  email: string | undefined;
  name: string | undefined;
  password: string | undefined;
  token: string | null;
  loggingOut: boolean; // flag set on logout to know to redirect after logout
  nextURL: string | null; // will probably remove this and find a better solution to login redirects
  gAuth: any;
  avatar: string;
  predictorCollections: PredictorCollection[];
*/

interface ProfileProps {
  auth: AuthStoreState;
  draftProfile: ProfileState;
}

const formItemLayout = {
  wrapperCol: {
    xs: { span: 24 },
    sm: { span: 8 },
  }
};

class Profile extends React.Component<ProfileProps, {}> {
  render() {
    let auth = this.props.auth;
    let draftProfile = this.props.draftProfile;

    return (
    <div>
      <Row type="flex" justify="center" style={{ background: '#fff', padding: 0 }}>
        <MainCol>
          <div>
            Email:<Space />
            {auth.email}
            <Space />
            <Switch
              checked={('' + draftProfile.public_email) === 'true'}
              checkedChildren="Public"
              unCheckedChildren="Private"
              onChange={checked => draftProfile.update({'public_email': '' + checked})}
            />
            <br/>
            Avatar: {auth.avatar}<br/>
            <Form {...formItemLayout} layout="vertical">
              <Form.Item label="Name" required={true}>
                <Input
                  value={!!draftProfile.name ? draftProfile.name : undefined}
                  required={true}
                  min={1}
                  onChange={(e) => draftProfile.update({name: e.currentTarget.value})}
                />
              </Form.Item>
              <Form.Item label="Institution">
                <Input
                  defaultValue={auth.institution}
                  value={draftProfile.institution}
                  onChange={(e) => draftProfile.update({institution: e.currentTarget.value})}
                />
              </Form.Item>
              <Form.Item label="ORCID iD">
                <Input
                  defaultValue={auth.orcid}
                  value={draftProfile.orcid}
                  onChange={(e) => draftProfile.update({orcid: e.currentTarget.value})}
                />
              </Form.Item>
              <Form.Item label="Bio">
                <Input.TextArea
                  defaultValue={auth.bio}
                  value={draftProfile.bio}
                  rows={4}
                  onChange={(e) => draftProfile.update({bio: e.currentTarget.value})}
                />
              </Form.Item>
              <Form.Item label="Twitter Handle">
                <Input
                  defaultValue={auth.twitter_handle}
                  value={draftProfile.twitter_handle}
                  onChange={(e) => draftProfile.update({twitter_handle: e.currentTarget.value})}
                />
              </Form.Item>
              <Form.Item label="Personal Site">
                <Input
                  defaultValue={auth.personal_site}
                  value={draftProfile.personal_site}
                  onChange={(e) => draftProfile.update({personal_site: e.currentTarget.value})}
                />
              </Form.Item>
            </Form>
          <Button
            type="primary"
            onClick={() => {
              api.updateProfile(profileEditItems.reduce(
                (acc, curr) => {acc[curr] = draftProfile[curr]; return acc; },
                {}
              ));
            }}
            size={'small'}
          >
            Update Profile
          </Button>
          </div>
        </MainCol>
      </Row>
    </div>
    );
  }
}

export default Profile;
