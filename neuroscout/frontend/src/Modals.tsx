import * as React from 'react';
import { Button, Divider, Form, Icon, Input, Modal } from 'antd';
import { GoogleLogin } from 'react-google-login';

import { config } from './config';
import { UserStore } from './user';

const FormItem = Form.Item;
const GOOGLECLIENTID = config.google_client_id;

class GoogleLoginBtn extends React.Component<UserStore, {}> {
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
            this.props.update({
              password: (e as any).tokenId,
              gAuth: e,
              isGAuth: true,
              openSignup: false,
              openLogin: false,
            });
            this.props.profile.update({
              email: (e as any).profileObj.email,
              picture: (e as any).profileObj.imageUrl
            });
            this.props.login();
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

export class ResetPasswordModal extends React.Component<UserStore, {}> {
  render() {
    return (
      <Modal
        title="Reset password"
        visible={this.props.openReset}
        footer={null}
        maskClosable={true}
        onCancel={e => {
          this.props.update({openReset: false});
        }}
      >
        <p>
         Please enter an email address to send reset instructions
        </p>
        <Form
          onSubmit={e => {
            e.preventDefault();
            this.props.resetPassword();
          }}
        >
          <FormItem>
            <Input
              prefix={<Icon type="mail" style={{ fontSize: 13 }}/>}
              placeholder="Email"
              type="email"
              size="large"
              value={this.props.profile.email}
              onChange={(e) => this.props.updateFromInput('email', e, true)}
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

export class EnterResetTokenModal extends React.Component<UserStore, {}> {
  render () {
    return (
      <Modal
        title="Change password"
        visible={this.props.openEnterResetToken}
        footer={null}
        maskClosable={true}
        onCancel={e => {
          this.props.update({ openEnterResetToken: false });
        }}
      >
        <p>
         We have sent a reset token to {this.props.profile.email} <br/>
         Please enter the token below, along with a new password for the account.
       </p>
        <Form
          onSubmit={e => {
            e.preventDefault();
            this.props.submitToken();
          }}
        >
          <FormItem>
            <Input
              prefix={<Icon type="tags" style={{ fontSize: 13 }}/>}
              placeholder="Token"
              type="token"
              size="large"
              onChange={(e) => this.props.updateFromInput('token', e)}

            />
          </FormItem>
          <FormItem>
            <Input
              prefix={<Icon type="lock" style={{ fontSize: 13 }}/>}
              placeholder="Password"
              type="password"
              size="large"
              onChange={(e) => this.props.updateFromInput('password', e)}
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

export class LoginModal extends React.Component<UserStore, {}> {
  render () {
    return (
      <Modal
        title="Log into Neuroscout"
        visible={this.props.openLogin}
        footer={null}
        maskClosable={true}
        onCancel={e => {
          this.props.logout();
          this.props.update({ openLogin: false });
        }}
      >
        <p>
          {this.props.loginError ? this.props.loginError : ''}
        </p>
        <br />
        <Form
          onSubmit={e => {
            e.preventDefault();
            this.props.login();
          }}
        >
          <FormItem>
            <Input
              prefix={<Icon type="mail" style={{ fontSize: 13 }}/>}
              placeholder="Email"
              type="email"
              size="large"
              value={this.props.profile.email}
              onChange={(e) => {
                this.props.updateFromInput('email', e, true);
              }}
            />
          </FormItem>
          <FormItem>
            <Input
              prefix={<Icon type="lock" style={{ fontSize: 13 }}/>}
              placeholder="Password"
              type="password"
              value={this.props.password}
              onChange={(e) => this.props.updateFromInput('password', e)}
            />
          </FormItem>
          <FormItem>
           <a onClick={e => {this.props.update( { openLogin: false, openReset: true}); }}>Forgot password</a><br/>
            <Button style={{ width: '100%' }} htmlType="submit" type="primary">
              Log in
            </Button>
          </FormItem>
        </Form>
        <Divider> Or log in with Google </Divider>
        <GoogleLoginBtn {...this.props} />
      </Modal>
    );
  }
}

export class SignupModal extends React.Component<UserStore, {}> {
  render() {
    return (
      <Modal
        title="Sign up for a Neuroscout account"
        visible={this.props.openSignup}
        footer={null}
        maskClosable={true}
        onCancel={e => this.props.update({ openSignup: false })}
      >
        <p>
          {this.props.signupError}
        </p>
        <br />
        <Form
          onSubmit={e => {
            e.preventDefault();
            this.props.signup();
          }}
        >
          <FormItem>
            <Input
              placeholder="Full name"
              size="large"
              value={this.props.profile.name}
              onChange={(e) => this.props.updateFromInput('name', e, true)}
            />
          </FormItem>
          <FormItem>
            <Input
              placeholder="Email"
              type="email"
              size="large"
              value={this.props.profile.email}
              onChange={(e) => this.props.updateFromInput('email', e, true)}
            />
          </FormItem>
          <FormItem>
            <Input
              placeholder="Password"
              type="password"
              value={this.props.password}
              onChange={(e) => this.props.updateFromInput('password', e)}
            />
          </FormItem>
          <FormItem>
            <Button style={{ width: '100%' }} type="primary" htmlType="submit">
              Sign up
            </Button>
          </FormItem>
        </Form>
        <Divider> Or sign up using a Google account </Divider>
        <GoogleLoginBtn {...this.props} />
      </Modal>
    );
  }
}
