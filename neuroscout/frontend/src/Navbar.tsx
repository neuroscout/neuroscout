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
  render(): JSX.Element {
    return (
      <Row justify="center" style={{ padding: 0 }}>
        <MainCol>
          <Menu
            mode="horizontal"
            style={{ lineHeight: '64px', justifyContent: 'flex-end' }}
            selectedKeys={[]}
          >
            <Menu.Item style={{ marginRight: 'auto' }} key="home">
              <Link to="/" style={{ fontSize: 20 }}>
                Neuroscout
              </Link>
            </Menu.Item>
            {this.props.loggedIn && (
              <Menu.Item key="create" className="newAnalysis">
                <Link to={{ pathname: '/builder' }}>
                  <PlusOutlined />
                  <Space />
                  New Analysis
                </Link>
              </Menu.Item>
            )}

            <Menu.SubMenu
              key="browse"
              className="browseMain"
              title={
                <span>
                  <SearchOutlined />
                  <Space />
                  Browse
                </span>
              }
            >
              {this.props.loggedIn && (
                <Menu.Item key="mine">
                  <Link to="/myanalyses">My Analyses</Link>
                </Menu.Item>
              )}
              <Menu.Item key="public">
                <Link to="/public">Public Analyses</Link>
              </Menu.Item>
              <Menu.Item key="predictors">
                <Link to="/predictors">All Predictors</Link>
              </Menu.Item>
              <Menu.Item key="datasets">
                <Link to="/datasets">All Datasets</Link>
              </Menu.Item>
            </Menu.SubMenu>
            <Menu.SubMenu
              key="help"
              title={
                <span>
                  <QuestionCircleOutlined />
                  <Space />
                  Help
                </span>
              }
            >
              <Menu.Item key="docs">
                <a
                  href="https://neuroscout.org/docs"
                  target="_blank"
                  rel="noreferrer"
                >
                  Documentation
                </a>
              </Menu.Item>
              <Menu.Item key="tour">
                <Link
                  to="/"
                  onClick={e => this.props.update({ openTour: true })}
                >
                  Start tour
                </Link>
              </Menu.Item>
              <Menu.Item key="askAQuestion">
                <a
                  href="https://neurostars.org/tag/neuroscout"
                  target="_blank"
                  rel="noreferrer"
                >
                  Ask a question
                </a>
              </Menu.Item>
            </Menu.SubMenu>
            {this.props.loggedIn === false && (
              <Menu.Item
                onClick={e => this.props.update({ openLogin: true })}
                key="signin"
              >
                Sign in
              </Menu.Item>
            )}
            {this.props.loggedIn ? (
              <Menu.SubMenu
                title={
                  <Avatar
                    shape="circle"
                    icon={<UserOutlined />}
                    src={this.props.profile.picture}
                    className="headerAvatar"
                  />
                }
              >
                <Menu.ItemGroup
                  title={`${
                    this.props.gAuth
                      ? String(this.props.gAuth.profileObj.email)
                      : String(this.props.profile.email)
                  }`}
                >
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
                    }}
                  >
                    Sign Out
                  </Menu.Item>
                </Menu.ItemGroup>
              </Menu.SubMenu>
            ) : (
              <Menu.Item key="signup">
                <Button
                  size="large"
                  type="primary"
                  onClick={e => this.props.update({ openSignup: true })}
                >
                  Sign up
                </Button>
              </Menu.Item>
            )}
          </Menu>
        </MainCol>
      </Row>
    )
  }
}

export default Navbar
