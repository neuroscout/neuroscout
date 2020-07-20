import * as React from 'react';
import { Avatar, Row, Button, Menu, Icon } from 'antd';
import { Link } from 'react-router-dom';

import { MainCol } from './HelperComponents';
import { UserStore } from './user';

class Navbar extends React.Component<UserStore, {}> {
  render() {
    return (
      <Row type="flex" justify="center" style={{padding: 0 }}>
        <MainCol>
          <Menu
            mode="horizontal"
            style={{ lineHeight: '64px'}}
            selectedKeys={[]}
          >
            <Menu.Item key="home">
               <Link to="/" style={{fontSize: 20}}>Neuroscout</Link>
            </Menu.Item>
            {this.props.loggedIn ?
              <Menu.SubMenu
                style={{float: 'right'}}
                title={
                  <Avatar
                    shape="circle"
                    icon="user"
                    src={this.props.profile.picture}
                    className="headerAvatar"
                  />
                }
              >
                 <Menu.ItemGroup title={`${this.props.gAuth ? this.props.gAuth.profileObj.email : this.props.profile.email}`}>
                   <Menu.Divider/>
                   <Menu.Item key="profile">
                     <Link to={`/profile/${this.props.profile.id}`}> My Profile </Link>
                   </Menu.Item>

                   <Menu.Item key="predictorCollections">
                     <Link to="/mycollections"> My Predictors </Link>
                   </Menu.Item>

                   <Menu.Item
                    key="signout"
                    onClick={(e) => {return this.props.confirmLogout(); }}
                   >
                    Sign Out
                   </Menu.Item>
                 </Menu.ItemGroup>
              </Menu.SubMenu>
             :
              <Menu.Item key="signup" style={{float: 'right'}}>
              <Button size="large" type="primary" onClick={e => this.props.update({ openSignup: true })}>
                Sign up</Button></Menu.Item>
             }
             {this.props.loggedIn === false &&
                 <Menu.Item
                  onClick={e => this.props.update({ openLogin: true })}
                  key="signin"
                  style={{float: 'right'}}
                 >
                   Sign in
                 </Menu.Item>
              }
             <Menu.Item
              style={{float: 'right'}}
              key="help"
             >
               <a href="https://neuroscout.github.io/neuroscout/"><span>
               <Icon type="question-circle"/>Help</span></a>
             </Menu.Item>

             <Menu.SubMenu
              style={{float: 'right'}}
              key="browse"
              className="browseMain"
              title={<span><Icon type="search"/>Browse</span>}
             >
               {this.props.loggedIn &&
                 <Menu.Item key="mine" >
                  <Link to="/myanalyses">
                    My analyses
                  </Link>
                 </Menu.Item>
              }
               <Menu.Item
                key="public"
               >
               <Link to="/public">
                Public analyses
                </Link>
               </Menu.Item>
             </Menu.SubMenu>

             {this.props.loggedIn &&
               <Menu.Item key="create" style={{float: 'right'}} className="newAnalysis">
                 <Link
                   to={{pathname: '/builder'}}
                 >
                   <Icon type="plus" /> New Analysis
                 </Link>
               </Menu.Item>
             }
          </Menu>
        </MainCol>
      </Row>
    );
  }
}

export default Navbar;
