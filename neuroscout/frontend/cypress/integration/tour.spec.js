describe('Tour', () => {
  it('opens tour', () => {
    cy.visit('/')
    cy.login('user@example.com', 'string')
    cy.wait(100)
    cy.get('.ant-btn-primary').contains('Tour!').click()
  })
})
