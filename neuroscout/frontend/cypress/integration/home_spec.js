describe('The Home Page', () => {
  it('successfully loads', () => {
    cy.visit('/')
  })

  it('navigation bar contents', () => {
    cy.get('.ant-menu').contains('Neuroscout').should('have.attr', 'href', '/')
    cy.get('.ant-menu').contains('Browse')
    cy.get('.ant-menu').not('Public Analyses')
    cy.get('.ant-menu').contains('Browse').click()
    cy.get('.ant-menu').contains('Browse').trigger('mouseover')
    cy.wait(100)
    cy.get('.ant-menu')
      .contains('Public Analyses')
      .should('have.attr', 'href', '/public')
    cy.get('.ant-menu').not('My Analyses')
    cy.get('li').contains('Help').trigger('mouseover')
    cy.wait(200)
    cy.get('a').contains('Documentation').should('have.attr', 'href', 'https://neuroscout.github.io/neuroscout/')
    cy.get('.ant-menu').contains('Sign in')
    cy.get('.ant-menu').contains('Sign up')
  })

  it('splash page contents', () => {
    cy.get('.splashLogo').should('have.length', 4)
    cy.contains(
      'A platform for fast and flexible re-analysis of (naturalistic) fMRI studies',
    )
    cy.get('.ant-btn')
      .contains('Browse public analyses')
      .parent()
      .should('have.attr', 'href', '/public')
    cy.get('.ant-btn')
      .contains('Learn more')
      .parent()
      .should('have.attr', 'href', 'https://neuroscout.github.io/neuroscout/')
  })

  it('test sign up button 1', () => {
    cy.get('.ant-modal-content').should('not.exist')
    cy.get('.ant-btn').contains('Sign up to get started!').parent().click()
    cy.get('.ant-modal-content')
    cy.contains('Sign up for a Neuroscout account')
    cy.get('.ant-modal-close-x').click()
    cy.get('.ant-modal-content').should('not.exist')
  })

  it('test sign up button 2', () => {
    cy.get('.ant-modal-content').should('not.exist')
    cy.get('.ant-btn').contains('Sign up').parent().click()
    cy.get('.ant-modal-content')
    cy.contains('Sign up for a Neuroscout account')
    cy.get('.ant-modal-close-x').click()
    cy.get('.ant-modal-content').should('not.exist')
  })

  it('test sign in button', () => {
    cy.get('.ant-modal-content').should('not.exist')
    cy.get('.ant-menu').contains('Sign in').click()
    cy.get('.ant-modal-content')
    cy.contains('Log into Neuroscout')
    cy.get('.ant-modal-close-x').click()
    cy.get('.ant-modal-content').should('not.exist')
  })
})
