import * as React from 'react'
import {
  PlusOutlined,
  QuestionCircleOutlined,
  SearchOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Avatar, Row, Button, Menu } from 'antd'
import { Link } from 'react-router-dom'

import { MainCol, Space } from './HelperComponents'
import { UserStore } from './user'

class Navbar extends React.Component<UserStore, Record<string, never>> {
  render() {
    return (
      <Row justify="center" style={{ padding: 0 }}>
        <MainCol>
          <Menu
            mode="horizontal"
            style={{ lineHeight: '64px' }}
            selectedKeys={[]}>
            <Menu.Item key="home">
              <Link to="/" style={{ fontSize: 20 }}>
                Neuroscout
              </Link>
            </Menu.Item>
            {this.props.loggedIn ? (
              <Menu.SubMenu
                style={{ float: 'right' }}
                title={
                  <Avatar
                    shape="circle"
                    icon={<UserOutlined />}
                    src={this.props.profile.picture}
                    className="headerAvatar"
                  />
                }>
                <Menu.ItemGroup
                  title={`${
                    this.props.gAuth
                      ? String(this.props.gAuth.profileObj.email)
                      : String(this.props.profile.email)
                  }`}>
                  <Menu.Divider />
                  <Menu.Item key="profile">
                    <Link to={`/profile/${this.props.profile.user_name}`}>
                      {' '}
                      My Profile{' '}
                    </Link>
                  </Menu.Item>

                  <Menu.Item key="predictorCollections">
                    <Link to="/mycollections"> My Predictors </Link>
                  </Menu.Item>

                  <Menu.Item
                    key="signout"
                    onClick={e => {
                      return this.props.confirmLogout()
                    }}>
                    Sign Out
                  </Menu.Item>
                </Menu.ItemGroup>
              </Menu.SubMenu>
            ) : (
              <Menu.Item key="signup" style={{ float: 'right' }}>
                <Button
                  size="large"
                  type="primary"
                  onClick={e => this.props.update({ openSignup: true })}>
                  Sign up
                </Button>
              </Menu.Item>
            )}
            {this.props.loggedIn === false && (
              <Menu.Item
                onClick={e => this.props.update({ openLogin: true })}
                key="signin"
                style={{ float: 'right' }}>
                Sign in
              </Menu.Item>
            )}
            <Menu.Item style={{ float: 'right' }} key="help">
              <a
                href="https://neuroscout.github.io/neuroscout/"
                target="_blank"
                rel="noreferrer">
                <span>
                  <QuestionCircleOutlined />
                  <Space />
                  Help
                </span>
              </a>
            </Menu.Item>

            <Menu.SubMenu
              style={{ float: 'right' }}
              key="browse"
              className="browseMain"
              title={
                <span>
                  <SearchOutlined />
                  <Space />
                  Browse
                </span>
              }>
              {this.props.loggedIn && (
                <Menu.Item key="mine">
                  <Link to="/myanalyses">My analyses</Link>
                </Menu.Item>
              )}
              <Menu.Item key="public">
                <Link to="/public">Public analyses</Link>
              </Menu.Item>
            </Menu.SubMenu>

            {this.props.loggedIn && (
              <Menu.Item
                key="create"
                style={{ float: 'right' }}
                className="newAnalysis">
                <Link to={{ pathname: '/builder' }}>
                  <PlusOutlined />
                  <Space />
                  New Analysis
                </Link>
              </Menu.Item>
            )}
          </Menu>
        </MainCol>
      </Row>
    )
  }
}

export default Navbar
