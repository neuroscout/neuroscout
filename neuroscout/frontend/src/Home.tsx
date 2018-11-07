/*
 Home component for the homepage
*/
import * as React from 'react';
import { Tabs, Row, Col, Button, Card } from 'antd';
import { displayError } from './utils';
import { MainCol, Space } from './HelperComponents';
import { AppAnalysis } from './coretypes';
import { Link } from 'react-router-dom';
import AnalysisList, { AnalysisListProps } from './AnalysisList';

interface HomeProps extends AnalysisListProps {
  loggedIn: boolean;
}

class Home extends React.Component<HomeProps, {}> {
  render() {
    const { analyses, cloneAnalysis, onDelete, loggedIn, publicList } = this.props;
    const listProps: AnalysisListProps = { ...this.props, publicList: loggedIn === false };
    return (
      <div>
      <Row type="flex" justify="center" style={{ background: '#fff', padding: 0 }}>
        <MainCol>
        <div>
         <img className="splashLogo" src="/Neuroscout_Simple_Wide.svg"/><br/>
         <p className="splashText">A platform for fast and flexible re-analysis of (naturalistic) fMRI studies
</p>
         </div>
        </MainCol>
        </Row>

        <Row type="flex" justify="center" style={{ background: '#fff', padding: 0 }}>
          <MainCol>
            <div>
              {!!analyses &&
                analyses.length > 0 &&
                <div>
                  <br />
                  {loggedIn ?
                    <h3>Your saved analyses:</h3>
                  :
                    <h3>Browse public analyses:</h3>
                  }

                  <br />
                  <AnalysisList {...listProps} />
                </div>}
               {loggedIn && analyses.length === 0 &&
                <p> WTF NO Analyses mate</p>}
            </div>
       </MainCol>
      </Row>
     </div>
    );
  }
}

export default Home;
