import * as React from 'react';
import { Route, Link, Redirect, Switch } from 'react-router-dom';
import { message } from 'antd';

import NotFound from './404';
import './css/App.css';
import { api } from './api';
import { AuthStore } from './auth.store';
import { authActions } from './auth.actions';
import AnalysisBuilder from './analysis_builder/Builder';
import { config } from './config';
import { ApiUser, ApiAnalysis, AppAnalysis, AuthStoreState, Dataset, AppState } from './coretypes';
import FAQ from './FAQ';
import { MainCol, Space } from './HelperComponents';
import Home from './Home';
import Private from './Private';
import Public from './Public';
import { displayError, jwtFetch, timeout } from './utils';

export default class Routes extends React.Component<AppState, {}> {
  render() {
    return (
      <Switch>
        <Route
          exact={true}
          path="/"
          render={props =>
            <Home />
           }
        />
        <Route
          exact={true}
          path="/builder"
          render={props => {
            // This is a temporary solution to prevent non logged-in users from entering the builder.
            // Longer term to automatically redirect the user to the target URL after login we
            // need to implement something like the auth workflow example here:
            // https://reacttraining.com/react-router/web/example/auth-workflow
            if (this.props.auth.loggedIn || this.props.auth.openLogin) {
              return <AnalysisBuilder
                        key={props.location.key}
                        datasets={this.props.datasets}
              />;
            }
            message.warning('Please log in first and try again');
            return <Redirect to="/" />;
          }}
        />
        <Route
          path="/builder/:id"
          render={props =>
            <AnalysisBuilder
              id={props.match.params.id}
              userOwns={this.props.analyses.filter((x) => x.id === props.match.params.id).length > 0}
              datasets={this.props.datasets}
            />}
        />
        <Route
          exact={true}
          path="/public/:id"
          render={props =>
            <AnalysisBuilder
              id={props.match.params.id}
              userOwns={this.props.analyses.filter((x) => x.id === props.match.params.id).length > 0}
              datasets={this.props.datasets}
            />
          }
        />
      <Route
        exact={true}
        path="/public"
        render={props =>
          <Public
            analyses={this.props.publicAnalyses}
            cloneAnalysis={this.props.cloneAnalysis}
            datasets={this.props.datasets}
          />}
      />
      <Route
        exact={true}
        path="/myanalyses"
        render={props =>
          <Private
            analyses={this.props.analyses}
            cloneAnalysis={this.props.cloneAnalysis}
            onDelete={this.props.onDelete}
            datasets={this.props.datasets}
          />}
      />
      <Route
        exact={true}
        path="/faq"
        render={() => <FAQ/>}
      />
      <Route render={() => <NotFound/>} />
      </Switch>
    );
  }
}
