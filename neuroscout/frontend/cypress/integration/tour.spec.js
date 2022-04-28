describe('Tour', () => {
  it('opens tour', () => {
    cy.visit('/')
    cy.get('li').contains('Help').trigger('mouseover')
    cy.wait(500)
    cy.get('a').contains('Start Tour').click()
    cy.get('div').contains('go on a tour!')
  })
})
