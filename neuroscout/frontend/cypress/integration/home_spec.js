describe('The Home Page', () => {
  it('successfully loads', () => {
    cy.visit('/') // change URL to match your dev URL
  })

  it('navigation bar contents', () =>{
    cy.get('.ant-menu').contains('Neuroscout')
    cy.get('.ant-menu').contains('Browse')
    cy.get('.ant-menu').not('Public analyses')
    cy.get('.ant-menu').contains('Browse').click()
    cy.get('.ant-menu').contains('Browse').trigger('mouseover')
    cy.wait(100)
    cy.get('.ant-menu').contains('Public analyses')
    cy.get('.ant-menu').not('My analyses')
    cy.get('.ant-menu').contains('Help')
    cy.get('.ant-menu').contains('Sign in')
    cy.get('.ant-menu').contains('Sign up')

    // Need to also check URLs etc...
  })

  it('splash page contents', () => {
    cy.get('.splashLogo').should('have.length', 4)
    cy.contains('A platform for fast and flexible re-analysis of (naturalistic) fMRI studies')
    cy.get('.ant-btn').contains('Browse public analyses').parent().should(
      'have.attr', 'href', '/public')
    cy.get('.ant-btn').contains('Learn more')

  })

  it('test login button 1', () => {
    cy.get('.ant-modal-content').should('not.exist')
    cy.get('.ant-btn').contains('Sign up to get started!').parent().click()
    cy.get('.ant-modal-content')
    cy.contains("Sign up for a Neuroscout account")
    cy.get('.ant-modal-close-x').click()
    cy.get('.ant-modal-content').should('not.exist')

  })

  it('test login button 2', () => {
    cy.get('.ant-modal-content').should('not.exist')
    cy.get('.ant-btn').contains('Sign up').parent().click()
    cy.get('.ant-modal-content')
    cy.contains("Sign up for a Neuroscout account")
    cy.get('.ant-modal-close-x').click()
    cy.get('.ant-modal-content').should('not.exist')
  })


})
