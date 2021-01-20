describe('Analysis Builder', () => {
  beforeEach(() => {
    cy.login('user@example.com', 'string')
    cy.get('.newAnalysis > a')
    cy.visit('/builder')
  })

  let name = 'dataset_name';
  let predCount = 3;
  it('analysis builder', () => {
    /* Overview Tab */
    cy.get('.builderAnalysisNameInput').type(name)
    cy.get(`.ant-col > .ant-input[value=${name}]`)
    cy.get('.builderAnalysisDescriptionInput').type(name)
    cy.get('.ant-form-item-children > .ant-input').contains(name)

    cy.get('.selectDataset')
    cy.get('td').contains('Test Dataset').parent().within(() => {
      cy.get('input[type=radio]').click()

    })
    cy.get('.builderAnalysisTaskSelect')
    cy.get('.ant-collapse-item > .ant-collapse-header').contains('Runs: All selected').click()
    cy.get('.builderAnalysisRunsSelect')
    cy.get('.ant-collapse-item-active > .ant-collapse-content > .ant-collapse-content-box').find('tr').its('length').should('be.gte', 1)
    cy.contains('Next').click()

    /* Predictor Tab - select first 3 predictors */
    let count = 0
    cy.contains('Select Predictors').parent().within(() => {
      cy.contains('Brightness')
      cy.get('.ant-table-body').find('input[type=checkbox]').each(($el, index, $list) => {
        if (count < predCount) {
          $el.click()
          count++
        }
      })
    })
    cy.get('.ant-tag').its('length').should('be.gte', predCount)
    cy.get('button:visible').contains('Next').parent().click()

    /* Transformation Tab - create a scale xform with all predictors */
    cy.get('button').contains('Add Transformation').parent().click()
    cy.get('.ant-select').click()
    cy.get('li').contains('Scale').click()
    cy.get('.ant-table-body:visible').find('input[type=checkbox]').each(($el, index, $list) => {
      $el.click()
    })
    cy.get('button:visible').contains('OK').parent().click()
    cy.get('button:visible').contains('Next').parent().click()
    let xformCount = 2

    /* HRF Tab - select all non counfound predictors, check length is correct */
    cy.get('button').contains('Select All Non-Confound').parent().click()
    cy.get('.ant-tag:visible').its('length').should('be.eq', predCount + 1)
    cy.get('button:visible').contains('Next').parent().click()

    /* Contrast Tab - generate dummy contrasts, then delete one of them */
    cy.get('button').contains('Generate Dummy').parent().click()
    cy.get('.ant-list:visible').find('.ant-btn-danger').its('length').should('be.eq', predCount)
    cy.get('.ant-list:visible').find('.ant-btn-danger').first().click()
    cy.get('.ant-list:visible').find('.ant-btn-danger').its('length').should('be.eq', predCount - 1)
    cy.get('button:visible').contains('Next').parent().click()

    /* Review Tab
        - Ensure the number of contrasts in summary section matches what we expect.
        - Intercept call to generate design matrix, reply with known good response.
        - ensure that vega embed is displayed
     */
    cy.get('.ant-collapse-item').contains('Contrasts').click()
    cy.get('.ant-collapse-item').contains('Contrasts').parent().find('.ant-collapse-content-box > div').children().should('have.length', predCount - 1)
    cy.get('.ant-collapse-item').contains('Transformations').click()
    cy.get('.ant-collapse-item').contains('Transformations').parent().find('.ant-collapse-content-box > div').children().should('have.length', xformCount)
    cy.get('.ant-spin-spinning:visible')
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
        - confirm in popup modal
        - ensure transition to pending status after we confirm submit
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

    cy.get('.ant-modal-body').contains('submit the analysis').get('button').contains('Yes').parent().click()

    cy.contains('Analysis Pending Generation')
  });
});
