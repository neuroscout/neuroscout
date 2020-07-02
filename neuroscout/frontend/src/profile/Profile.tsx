import * as React from 'react';
import { Divider, Row, Col, Button, Card, Form, Input } from 'antd';
import { MainCol } from '../HelperComponents';

import { AuthStoreState } from '../coretypes';
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

interface ProfileState {
  name: string | undefined;
  institution: string | undefined;
}

interface ProfileProps {
  auth: AuthStoreState;
}

const formItemLayout = {
  wrapperCol: {
    xs: { span: 24 },
    sm: { span: 8 },
  }
};

class Profile extends React.Component<ProfileProps, ProfileState> {
  constructor(props: ProfileProps) {
    super(props);
    this.state = {
      name: props.auth.name,
      institution: props.auth.institution
    };
  }

  update() {
    // Post changes to api.
    // Handle invalid username etc
    // If all good reload profile? or just kick changes up to top level state?
    let updates = {email: '', name: '', institution: '', ...this.state};
    let res = api.updateProfile(updates);
    // tslint:disable-next-line:no-console
    console.log(res);
    return;
  }

  render() {
    let auth = this.props.auth;
    // tslint:disable-next-line:no-console
    console.log(this.props);
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
                  placeholder="Display Name"
                  value={this.state.name}
                  onChange={(e) => this.setState({name: e.currentTarget.value})}
                  required={true}
                  min={1}
                />
              </Form.Item>
              <Form.Item label="Institution">
                <Input
                  value={this.state.institution}
                  onChange={(e) => this.setState({institution: e.currentTarget.value})}
                />
              </Form.Item>
            </Form>
          <Button type="primary" onClick={() => {this.update(); }} size={'small'}>
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
