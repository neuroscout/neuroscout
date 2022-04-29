describe('Tour', () => {
  it('opens tour', () => {
    cy.visit('/')
    cy.login('user@example.com', 'string')
    cy.wait(200)
    cy.get('#rainbow-btn').click()
  })
})
