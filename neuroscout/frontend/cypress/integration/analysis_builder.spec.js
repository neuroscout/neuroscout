describe('Analysis Builder', () => {
  beforeEach(() => {
    cy.login('user@example.com', 'string')
    cy.get('.newAnalysis > a')
    cy.visit('/builder')
  })

  let name = 'dataset_name';
  let predCount = 5;
  it('analysis builder', () => {
    /* Overview Tab */
    cy.get('.builderAnalysisNameInput').type(name)
    cy.get(`.ant-col > .ant-input[value=${name}]`)
    cy.get('.builderAnalysisDescriptionInput').type(name)
    cy.get('.ant-form-item-children > .ant-input').contains(name)

    cy.get('.selectDataset')
    cy.get('td').contains('Life').parent().within(() => {
      cy.get('input[type=radio]').click()
      
    })
    cy.get('.builderAnalysisTaskSelect')
    cy.get('.ant-collapse-item > .ant-collapse-header').contains('Runs: All selected').click()
    cy.get('.builderAnalysisRunsSelect')
    cy.get('.ant-collapse-item-active > .ant-collapse-content > .ant-collapse-content-box').find('tr').its('length').should('be.gte', 1)
    cy.contains('Next').click()

    /* Predictor Tab - select first 5 predictors */
    let count = 0
    cy.contains('Select Predictors').parent().within(() => {
      cy.contains('abstract')
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
    let xformCount = 1

    /* HRF Tab */
    cy.get('button').contains('Select All Non-Confound').parent().click()
    cy.get('.ant-tag:visible').its('length').should('be.eq', predCount + 1)
    cy.get('button:visible').contains('Next').parent().click()

    /* Contrast Tab - generate dummy contrasts, then delete one of them */
    cy.get('button').contains('Generate Dummy').parent().click()
    cy.get('.ant-list:visible').find('.ant-btn-danger').its('length').should('be.eq', predCount)
    cy.get('.ant-list:visible').find('.ant-btn-danger').first().click()
    cy.get('.ant-list:visible').find('.ant-btn-danger').its('length').should('be.eq', predCount - 1)
    cy.get('button:visible').contains('Next').parent().click()

    /* Review Tab */
    cy.get('.ant-collapse-item').contains('Contrasts').click()
    cy.get('.ant-collapse-item').contains('Contrasts').parent().find('.ant-collapse-content-box > div').children().should('have.length', predCount - 1)
    cy.get('.ant-collapse-item').contains('Transformations').click()
    cy.get('.ant-collapse-item').contains('Transformations').parent().find('.ant-collapse-content-box > div').children().should('have.length', xformCount)
    cy.get('.ant-spin-spinning:visible')
    cy.intercept('GET', '**/report**', 'fixture:design_matrix_response.json')
    cy.fixture('design_matrix_response.json').then(dmResponse => {
    })

    //cy.get('button:visible').contains('Next').parent().click()

    /* Status Tab */
    /*
    cy.get('.statusTOS').get('button:disabled')
    cy.get('span').contains('terms of service').parent().find('input').check()
    cy.get('.statusTOS').get('span:visible').contains('Generate').parent().click()
    */
  });
});
