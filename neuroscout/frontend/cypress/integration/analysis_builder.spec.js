describe('Analysis Builder', () => {
  beforeEach(() => {
    cy.login('user@example.com', 'string')
    cy.get('.newAnalysis > a')
    cy.visit('/builder')
  })

  let name = 'dataset_name';
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

    /* Predictor Tab */
    let count = 0
    cy.contains('Select Predictors').parent().within(() => {
      cy.contains('abstract')
      cy.get('.ant-table-body').find('input[type=checkbox]').each(($el, index, $list) => {
        if (count < 5) {
          $el.click()
          count++
        }
      })
    })
    cy.get('.ant-tag').its('length').should('be.gte', 5)
    cy.get('button:visible').contains('Next').parent().click()

    /* Transformation Tab */
    cy.get('button').contains('Add Transformation').parent().click()
    cy.get('.ant-select').click()
    cy.get('li').contains('Scale').click()
    cy.get('.ant-table-body:visible').find('input[type=checkbox]').each(($el, index, $list) => {
      $el.click()
    })
    cy.get('button:visible').contains('OK').parent().click()
    cy.get('button:visible').contains('Next').parent().click()

    /* HRF Tab */
  });
});
