Cypress.Commands.add("login", (email, password) => {
    cy.visit('/')
    cy.get('.ant-menu-item').contains('Sign in').click()
    cy.get('.ant-input[type=email]').type(email)
    cy.get('.ant-input[type=password]').type(password)
    cy.get('span').contains('Log in').click()
})
