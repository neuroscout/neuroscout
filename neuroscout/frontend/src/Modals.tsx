import * as React from 'react';
import { Button, Divider, Form, Icon, Input, Modal } from 'antd';
import { GoogleLogin } from 'react-google-login';

import { authActions } from './auth.actions';
import { config } from './config';
import { AuthStoreState } from './coretypes';

const FormItem = Form.Item;
const GOOGLECLIENTID = config.google_client_id;

class GoogleLoginBtn extends React.Component<{}, {}> {
  render() {
    return (
      <GoogleLogin
        clientId={GOOGLECLIENTID}
        render={renderProps => (
          <Button
            onClick={renderProps && renderProps.onClick}
            style={{ width: '100%' }}
            htmlType="submit"
            type="primary"
            ghost={true}
          >
            <Icon type="google" />
          </Button>
        )}
        buttonText="Log in"
        onSuccess={(e) => {
          if (e.hasOwnProperty('accessToken')) {
            authActions.update({
              email: (e as any).profileObj.email,
              password: (e as any).tokenId,
              gAuth: e,
              isGAuth: true,
              openSignup: false,
              openLogin: false,
              avatar: (e as any).profileObj.imageUrl
            });
            authActions.login();
          }
          return '';
        }}
        onFailure={(e) => {
          return '';
        }}
      />
    );
  }
}

export class ResetPasswordModal extends React.Component<AuthStoreState, {}> {
  render() {
    return (
      <Modal
        title="Reset password"
        visible={this.props.openReset}
        footer={null}
        maskClosable={true}
        onCancel={e => {
          authActions.update({openReset: false});
        }}
      >
        <p>
         Please enter an email address to send reset instructions
        </p>
        <Form
          onSubmit={e => {
            e.preventDefault();
            authActions.resetPassword();
          }}
        >
          <FormItem>
            <Input
              prefix={<Icon type="mail" style={{ fontSize: 13 }}/>}
              placeholder="Email"
              type="email"
              size="large"
              value={this.props.email}
              onChange={authActions.updateFromInput('email')}
            />
          </FormItem>
          <FormItem>
            <Button style={{ width: '100%' }} htmlType="submit" type="primary">
              Reset password
            </Button>
          </FormItem>
        </Form>
      </Modal>
    );
  }
}

export class EnterResetTokenModal extends React.Component<AuthStoreState, {}> {
  render () {
    return (
      <Modal
        title="Change password"
        visible={this.props.openEnterResetToken}
        footer={null}
        maskClosable={true}
        onCancel={e => {
          authActions.update({ openEnterResetToken: false });
        }}
      >
        <p>
         We have sent a reset token to {this.props.email} <br/>
         Please enter the token below, along with a new password for the account.
       </p>
        <Form
          onSubmit={e => {
            e.preventDefault();
            authActions.submitToken();
          }}
        >
          <FormItem>
            <Input
              prefix={<Icon type="tags" style={{ fontSize: 13 }}/>}
              placeholder="Token"
              type="token"
              size="large"
              onChange={authActions.updateFromInput('token')}

            />
          </FormItem>
          <FormItem>
            <Input
              prefix={<Icon type="lock" style={{ fontSize: 13 }}/>}
              placeholder="Password"
              type="password"
              size="large"
              onChange={authActions.updateFromInput('password')}
            />
          </FormItem>
          <FormItem>
            <Button style={{ width: '100%' }} htmlType="submit" type="primary">
              Submit
            </Button>
          </FormItem>
        </Form>
        <p>
          {this.props.resetError}
        </p>
        <br />
      </Modal>
    );
  }
}

export class LoginModal extends React.Component<AuthStoreState, {}> {
  render () {
    return (
      <Modal
        title="Log into Neuroscout"
        visible={this.props.openLogin}
        footer={null}
        maskClosable={true}
        onCancel={e => {
          authActions.logout();
          authActions.update({ openLogin: false });
        }}
      >
        <p>
          {this.props.loginError ? this.props.loginError : ''}
        </p>
        <br />
        <Form
          onSubmit={e => {
            e.preventDefault();
            authActions.login();
          }}
        >
          <FormItem>
            <Input
              prefix={<Icon type="mail" style={{ fontSize: 13 }}/>}
              placeholder="Email"
              type="email"
              size="large"
              value={this.props.email}
              onChange={(e) => {
                authActions.updateFromInput('email', e);
              }}
            />
          </FormItem>
          <FormItem>
            <Input
              prefix={<Icon type="lock" style={{ fontSize: 13 }}/>}
              placeholder="Password"
              type="password"
              value={this.props.password}
              onChange={(e) => authActions.updateFromInput('password', e)}
            />
          </FormItem>
          <FormItem>
           <a onClick={e => {authActions.update( { openLogin: false, openReset: true}); }}>Forgot password</a><br/>
            <Button style={{ width: '100%' }} htmlType="submit" type="primary">
              Log in
            </Button>
          </FormItem>
        </Form>
        <Divider> Or log in with Google </Divider>
        <GoogleLoginBtn />
      </Modal>
    );
  }
}

export class SignupModal extends React.Component<AuthStoreState, {}> {
  render() {
    return (
      <Modal
        title="Sign up for a Neuroscout account"
        visible={this.props.openSignup}
        footer={null}
        maskClosable={true}
        onCancel={e => authActions.update({ openSignup: false }, e)}
      >
        <p>
          {this.props.signupError}
        </p>
        <br />
        <Form
          onSubmit={e => {
            e.preventDefault();
            authActions.signup();
          }}
        >
          <FormItem>
            <Input
              placeholder="Full name"
              size="large"
              value={this.props.name}
              onChange={(e) => authActions.updateFromInput('name', e)}
            />
          </FormItem>
          <FormItem>
            <Input
              placeholder="Email"
              type="email"
              size="large"
              value={this.props.email}
              onChange={(e) => authActions.updateFromInput('email', e)}
            />
          </FormItem>
          <FormItem>
            <Input
              placeholder="Password"
              type="password"
              value={this.props.password}
              onChange={(e) => authActions.updateFromInput('password', e)}
            />
          </FormItem>
          <FormItem>
            <Button style={{ width: '100%' }} type="primary" htmlType="submit">
              Sign up
            </Button>
          </FormItem>
        </Form>
        <Divider> Or sign up using a Google account </Divider>
        <GoogleLoginBtn />
      </Modal>
    );
  }
}
