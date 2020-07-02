import * as React from 'react';
import { Divider, Row, Col, Button, Card, Form, Input } from 'antd';
import { MainCol } from '../HelperComponents';

import memoize from 'memoize-one';

import { AuthStoreState, ProfileState } from '../coretypes';
import { api } from '../api';

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
            Email: {auth.email}<br/>
            Avatar: {auth.avatar}<br/>
            <Form {...formItemLayout} layout="vertical">
              <Form.Item label="Name" required={true}>
                <Input
                  defaultValue={'wat'}
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
            </Form>
          <Button
            type="primary"
            onClick={() => {
              api.updateProfile({name: draftProfile.name, institution: draftProfile.institution });
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
