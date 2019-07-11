/*
Resuable AnalysisList component used for displaying a list of analyses, e.g. on
the home page or on the 'browse public analysis' page
*/
import * as React from 'react';
import { Button, Row, Table } from 'antd';
import { MainCol, Space } from './HelperComponents';
import { AppAnalysis, Dataset } from './coretypes';
import { Status } from './Status';
import { Link } from 'react-router-dom';

export interface AnalysisListProps {
  loggedIn?: boolean;
  publicList?: boolean;
  analyses: AppAnalysis[];
  cloneAnalysis: (id: string) => void;
  onDelete?: (analysis: AppAnalysis) => void;
  children?: React.ReactNode;
  datasets: Dataset[];
}

class AnalysisListTable extends React.Component<AnalysisListProps> {
  render() {
    const { analyses, datasets, publicList, cloneAnalysis, onDelete } = this.props;

    // Define columns of the analysis table
    // Open link: always (opens analysis in Builder)
    // Delete button: only if not a public list and analysis is in draft mode
    // Clone button: any analysis
    const analysisTableColumns = [
      {
        title: 'ID',
        dataIndex: 'id',
        sorter: (a, b) => a.id.localeCompare(b.id)
      },
      {
        title: 'Name',
        render: (text, record: AppAnalysis) => (
          <Link to={`/builder/${record.id}`}>
            <div className="recordName">{record.name}</div>
          </Link>
        ),
        sorter: (a, b) => a.name.localeCompare(b.name)
      },
      {
        title: 'Status',
        dataIndex: 'status',
        render: (text, record) => <Status status={record.status} />,
        sorter: (a, b) => a.status.localeCompare(b.status)
      },
      {
        title: 'Modified at',
        dataIndex: 'modifiedAt',
        defaultSortOrder: 'descend' as 'descend',
        sorter: (a, b) => a.modifiedAt.localeCompare(b.modifiedAt)
      },
      {
        title: 'Dataset',
        dataIndex: 'datasetName',
        render: (text, record) => {
          let dataset: any = datasets.filter((x) => {return x.id === text.toString(); } );
          let name = ' ';
          if (!!dataset && dataset.length === 1) {
            name = dataset[0].name;
          }
          return (<>{name}</>);
        },
        sorter: (a, b) => {
          let dataset: (Dataset | undefined) = datasets.find((x) => {return x.id === a.datasetName.toString(); } );
          a = (!!dataset && !!dataset.name) ? dataset.name : '';
          dataset = datasets.find((x) => {return x.id === b.datasetName.toString(); } );
          b = (!!dataset && !!dataset.name) ? dataset.name : '';
          return a.localeCompare(b);
        }
      },
      {
        title: 'Actions',
        render: (text, record: AppAnalysis) => (
          <span>
            {record.status === 'PASSED' && 
              <>
              <Button type="primary" ghost={true} onClick={() => cloneAnalysis(record.id)}>
                Clone
              </Button>
              <Space /></>}
            {!publicList &&
              ['DRAFT', 'FAILED'].includes(record.status) &&
              <Button type="danger" ghost={true} onClick={() => onDelete!(record)}>
                Delete
              </Button>}
          </span>
        )
      }
    ];
    return (
      <div>
        <Table
          columns={analysisTableColumns}
          rowKey="id"
          size="small"
          dataSource={analyses}
          expandedRowRender={record =>
            <p>
              {record.description}
            </p>}
          pagination={(analyses.length > 20) ? {'position': 'bottom'} : false}
        />
      </div>
    );
  }
}

// wrap table in components for use by itself as route
const AnalysisList = (props: AnalysisListProps) => {
  return (
    <div>
      <Row type="flex" justify="center">
        <MainCol>
        <h3>
          {props.publicList ? 'Public analyses' : 'Your saved analyses'}
        </h3>
          <br />
          <AnalysisListTable {...props} />
        </MainCol>
      </Row>
    </div>
  );
};

export default AnalysisList;
