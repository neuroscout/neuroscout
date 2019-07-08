import * as React from 'react';
import { Col, Collapse, Divider, Row } from 'antd';
import { MainCol } from './HelperComponents';

const Panel = Collapse.Panel;

const faqs = [
  [`Is this service free to use?`,
    `Yes! Note, however, that Neuroscout is a web-based engine for fMRI analysis specification; at the moment,
    we don't provide free computing resources for the execution of the resulting analysis bundles.`],
  [`How do I get more help?`,
   `Please see this page, and our tutorial, to learn about Neuroscout. Also, be aware that tooltips are
    provided throughout to clarify aspects of the user interface. For usage questions not addressed in the
    documentation, please open an issue on <a href="https://neurostars.org">NeuroStars</a>. For bug reports,
    feature requests, feedback, etc., please open an issue on
    <a href="https://github.com/neuroscout/neuroscout/issues"> GitHub</a>.`],
  [`Are there any restrictions on analyses I create on Neuroscout?`,
   `<p>
    Yes. By using Neuroscout, you agree that once you have finalized and "compiled" an analysis, the analysis
    can no longer be deleted from our system. If you wish to 'edit' an Analysis, you may clone the analysis,
    and make any desired changed on the forked version. Although analyses are by default not searchable by
    other users, any user with the private analysis ID may view your analysis.
    </p>
    Also, in the event that you publish any results generated using the NeuroScout interface, you MUST provide
    a link to the corresponding analysis page(s) on the NeuroScout website.`],
  [`I plan to publish results I've obtained using Neuroscout, how do I cite Neuroscout?`,
   `Please cite (zenodo link for now?), and be sure to include all relevant analysis IDs.`],
  [`I have a naturalistic study I'd like to share on Neuroscout, how do I do so?`,
   `Due to the financial cost of extracting features from multi-modal stimuli using external APIs, the set of
    datasets we support is manually curated. However, we are continually expanding the list of supported
    datasets, and we encourage researchers to contact us if they want to make their data available for use in
    Neuroscout. Note that it is much easier for us to ingest datasets that are already deposited in the
    <a href="https://openneuro.org"> OpenNeuro</a> repository, and we we strongly recommend uploading your
    dataset to <a href="https://openneuro.org"> OpenNeuro</a> whether or not it eventually ends up in
    Neuroscout.`],
  [`I want to make changes to an analysis I already ran, but it is locked. How can I edit it?`,
   `Once an analysis has been run, it is permanently locked and archived for provenance. You may "clone" your
    analysis, and make changes to this new copy of your analysis.`],
  [`I want to make one of my "private" analyses public, but the website says the analysis is "locked"!`,
   `When an analysis is locked, you can no longer make any substantive changes that affect model specification.
    However, you can always edit the name, description, and public/private status. So go ahead and make your
    analysis public!`],
  [`How do you automatically extract features from naturalistic datasets?`,
   `<p>
    The original stimuli presented to users are submitted to various machine learning algorithms and services
    to extract novel feature timecourses. To facility this process, we have developed a Python library for
    multimodal feature extraction called <a href="https://github.com/tyarkoni/pliers"> pliers</a>.
    Pliers allows us to extract a wide-variety of features across modalities using various external content
    analysis services with ease. For example, we are able to use Google Vision API to encode various
    aspects of the visual elements of movie frames, such as when a face is present. In addition, pliers
    allows us to easily link up various feature extraction services; for example, we can use the IBM Watson
    Speech to Text API to transcribe the speech in a movie into words with precise onsets, and then use a
    predefined dictionary of lexical norms to extract lexical norms for each word, such as frequency. We can
    then generate timecourses for each of these extracted features, creating novel predictors of brain
    activity.  For more information of pliers , please see the GitHub repository
    (<a href="https://github.com/tyarkoni/pliers">https://github.com/tyarkoni/pliers</a>) and the following
    paper:
    </p>
    <cite>
    McNamara, Q., De La Vega, A., & Yarkoni, T. (2017, August). Developing a comprehensive framework for
    multimodal feature extraction. In Proceedings of the 23rd ACM SIGKDD International Conference on Knowledge
    Discovery and Data Mining (pp. 1567-1574). ACM.
    </cite>`]
];

export default class FAQ extends React.Component<{}, {}> {

  render() {
    let faqsDisplay: any[] = [];
    faqs.map((x, i) => {
      faqsDisplay.push(
            <Panel header={x[0]} key={'' + i}>
              <div dangerouslySetInnerHTML={{__html: x[1]}} />
            </Panel>
      );
    });
    return (
      <Row type="flex" justify="center" style={{padding: 0 }}>
        <MainCol>
          <Collapse bordered={false}>
            {faqsDisplay}
          </Collapse>
        </MainCol>
      </Row>
    );
  }
}
