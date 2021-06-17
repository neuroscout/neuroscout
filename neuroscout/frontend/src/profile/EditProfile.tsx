import * as React from 'react'
import {
  Alert,
  message,
  Divider,
  Row,
  Col,
  Button,
  Card,
  Input,
  Switch,
  Form,
} from 'antd'
import { MainCol, Space } from '../HelperComponents'
import { withRouter } from 'react-router-dom'
import { RouteComponentProps } from 'react-router'

import memoize from 'memoize-one'

import { profileEditItems, ProfileState } from '../coretypes'
import { api } from '../api'

const formItemLayout = {
  wrapperCol: {
    xs: { span: 24 },
    sm: { span: 8 },
  },
}

class EditProfile extends React.Component<
  ProfileState & RouteComponentProps,
  ProfileState & { errors: string }
> {
  constructor(props) {
    super(props)
    this.state = { ...props, errors: '' }
  }

  profileLoaded = memoize((...args) => {
    this.setState({ ...this.props, errors: this.state.errors })
  })

  render() {
    this.profileLoaded(...profileEditItems.map(x => this.props[x]))
    return (
      <div>
        <Row justify="center" style={{ background: '#fff', padding: 0 }}>
          <MainCol>
            {this.state.errors && (
              <Row>
                <Col {...formItemLayout.wrapperCol}>
                  <Alert message={this.state.errors} type="error" />
                  <br />
                </Col>
              </Row>
            )}
            <div>
              Email:
              <Space />
              {this.state.email}
              <Space />
              <Switch
                checked={this.state.public_email === 'true'}
                checkedChildren="Public"
                unCheckedChildren="Private"
                onChange={checked =>
                  this.setState({ public_email: String(checked) })
                }
              />
              <br />
              {this.state.picture && (
                <>
                  Avatar: {this.state.picture}
                  <br />
                </>
              )}
              <Form {...formItemLayout} layout="vertical">
                <Form.Item label="Name" required>
                  <Input
                    value={this.state.name ? this.state.name : undefined}
                    required
                    min={1}
                    onChange={e =>
                      this.setState({ name: e.currentTarget.value })
                    }
                  />
                </Form.Item>
                <Form.Item label="Username" required>
                  <Input
                    value={
                      this.state.user_name ? this.state.user_name : undefined
                    }
                    required
                    min={1}
                    onChange={e =>
                      this.setState({ user_name: e.currentTarget.value })
                    }
                  />
                </Form.Item>
                <Form.Item label="Institution">
                  <Input
                    defaultValue={this.state.institution}
                    value={this.state.institution}
                    onChange={e =>
                      this.setState({ institution: e.currentTarget.value })
                    }
                  />
                </Form.Item>
                <Form.Item label="ORCID iD">
                  <Input
                    defaultValue={this.state.orcid}
                    value={this.state.orcid}
                    onChange={e =>
                      this.setState({ orcid: e.currentTarget.value })
                    }
                  />
                </Form.Item>
                <Form.Item label="Bio">
                  <Input.TextArea
                    defaultValue={this.state.bio}
                    value={this.state.bio}
                    rows={4}
                    onChange={e =>
                      this.setState({ bio: e.currentTarget.value })
                    }
                  />
                </Form.Item>
                <Form.Item label="Twitter Handle">
                  <Input
                    addonBefore="@"
                    value={this.state.twitter_handle}
                    onChange={e =>
                      this.setState({ twitter_handle: e.currentTarget.value })
                    }
                  />
                </Form.Item>
                <Form.Item label="Personal Site">
                  <Input
                    addonBefore="https://"
                    defaultValue={this.state.personal_site}
                    value={this.state.personal_site}
                    onChange={e =>
                      this.setState({ personal_site: e.currentTarget.value })
                    }
                  />
                </Form.Item>
              </Form>
              <Button
                type="primary"
                onClick={() => {
                  return api
                    .updateProfile(
                      profileEditItems.reduce((acc, curr) => {
                        acc[curr] = this.state[curr]
                        return acc
                      }, {}),
                    )
                    .then((ret: any) => {
                      let errorMessage = ''
                      if (ret && ret.statusCode === 200) {
                        void message.success('Profile updated.')
                        this.props.history.push(
                          `/profile/${this.state.user_name}`,
                        )
                        this.props.update(this.state)
                      } else if (ret && ret.statusCode === 422) {
                        if (ret.message) {
                          Object.keys(ret.message).forEach(key => {
                            errorMessage += String(ret.message[key]) + '; '
                          })
                        }
                        this.setState({ user_name: this.props.user_name })
                      }
                      this.setState({ errors: errorMessage })
                    })
                }}
                size={'small'}>
                Update Profile
              </Button>
            </div>
          </MainCol>
        </Row>
      </div>
    )
  }
}

export default withRouter(EditProfile)
