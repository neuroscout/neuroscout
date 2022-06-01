describe('Analysis Builder', () => {
  beforeEach(() => {
    /*
    cy.login('user@example.com', 'string')
    cy.get('.newAnalysis a')
    cy.visit('/builder')
    */
  })

  let name = 'dataset_name';
  let predCount = 3;
  it('analysis builder', () => {
    cy.login('user@example.com', 'string')
    cy.get('.newAnalysis a')
    cy.visit('/builder')

    /* Overview Tab */
    cy.get('.builderAnalysisNameInput').type(name)
    cy.get(`.ant-col > .ant-input[value=${name}]`)
    cy.get('.builderAnalysisDescriptionInput').type(name)
    cy.get('.builderAnalysisDescriptionInput').contains(name)

    cy.get('.selectDataset')
    cy.get('input[type=radio]').first().click()
    cy.get('.builderAnalysisTaskSelect')
    cy.get('.ant-collapse-item > .ant-collapse-header').contains('Runs: All selected').click()
    cy.get('.builderAnalysisRunsSelect')
    cy.get('.ant-collapse-item-active > .ant-collapse-content > .ant-collapse-content-box').find('tr').its('length').should('be.gte', 1)
    cy.contains('Next').click()

    /* Predictor Tab - select first 3 predictors */
    let count = 0
    cy.contains('Select Predictors').parent().within(() => {
      cy.contains('Brightness')
      cy.get('.ant-table-tbody').find('input[type=checkbox]').each(($el, index, $list) => {
        if (count < predCount) {
          $el.click()
          count++
        }
      })
    })
    cy.contains('Selected').click()
    cy.get('.ant-table-tbody').its('length').should('be.gte', predCount)
    cy.get('button:visible').contains('Next').parent().click()

    /* Transformation Tab - create a scale xform with all predictors */
    cy.get('button').contains('Add Transformation').parent().click()
    cy.get('.ant-form-item-control-input-content > .ant-select > .ant-select-selector').click()
    cy.get('.ant-select-item-option-content').contains('Scale').click()
    cy.get('.ant-table-body:visible').find('input[type=checkbox]').each(($el, index, $list) => {
      $el.click()
    })
    cy.get('button:visible').contains('OK').parent().click()
    cy.get('button:visible').contains('Next').parent().click()
    let xformCount = 1

    /* HRF Tab - select all non counfound predictors, check length is correct */
    cy.get('button').contains('Select All Non-Confound').parent().click()
    cy.get('#rc-tabs-0-panel-hrf').contains('Selected').click()
    cy.get('#rc-tabs-0-panel-hrf').get('.ant-table-tbody').its('length').should('be.gte', predCount)
    cy.get('button:visible').contains('Next').parent().click()

    /* Contrast Tab - generate dummy contrasts, then delete one of them */
    cy.get('button').contains('Generate Dummy').parent().click()
    cy.get('.ant-list:visible').find('.ant-btn-dangerous').its('length').should('be.eq', predCount)
    cy.get('.ant-list:visible').find('.ant-btn-dangerous').first().click()
    cy.get('.ant-list:visible').find('.ant-btn-dangerous').its('length').should('be.eq', predCount - 1)
    cy.get('button:visible').contains('Next').parent().click()

    /* Review Tab
        - Ensure the number of contrasts in summary section matches what we expect.
        - Intercept call to generate design matrix, reply with known good response.
        - ensure that vega embed is displayed
     */
    let dmResp;
    cy.fixture('design_matrix_response.json').then(dmBody => {
      dmResp = dmBody
    });
    cy.intercept('GET', '**/report**', (req) => {
      req.reply(dmResp)
    })
    cy.get('.vega-embed')
    cy.get('button:visible').contains('Next').parent().click()

    /* Status Tab
        - ensure that generate button disabled
        - toggle TOS checkbox
        - generate button should now be enabled, hit it
        - ensure transition to pending status after we submit
     */
    cy.get('.statusTOS').get('button:disabled')
    cy.get('span').contains('terms of service').parent().find('input').check()
    cy.get('.statusTOS').get('span:visible').contains('Generate').parent().click()
    cy.intercept('GET', '**/report**', (req) => {
      req.reply(dmResp)
    })
    cy.intercept('POST', '**/compile**', {
      statusCode: 200,
      body: {'status': 'SUBMITTING', 'traceback': ''}
    })
    cy.intercept('GET', '**/compile', {
      statusCode: 200,
      body: {'status': 'PENDING', 'traceback': ''}
    })

    cy.contains('Analysis Pending Generation')
  });
});
