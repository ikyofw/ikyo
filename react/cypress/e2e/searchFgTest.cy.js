/* eslint-disable no-undef */
Cypress.on("uncaught:exception", (err, runnable) => {
  // 返回 false 阻止 Cypress 因这个错误而失败
  return false
})

describe("searchFg", () => {
  it("type text", () => {
    cy.visit("http://localhost:3000/SearchFgDemo")

    cy.get("#__u").type("admin")
    cy.get("#__p").type("password")
    cy.get("#__login").click()
    cy.wait(5000)

    cy.get("#searchFg .fieldgroup_caption").should("exist").should("have.text", "Search")

    // cy.get("#searchFg .property_key").should("have.length", 5)
    // cy.get("#searchFg .property_value").should("have.length", 5)

    // text box
    cy.get("#searchFg .property_key").eq(0).should("have.text", "Text Box")
    cy.get("#searchFg .property_value").eq(0).find("input").should("have.value", "")
    cy.get("#searchFg .property_value").eq(0).find("input").type("test text").should("have.value", "test text")

    // combo box
    cy.get("#searchFg .property_key").eq(1).should("have.text", "Combo Box")
    cy.get("#searchFg .property_value").eq(1).find("select").find(":selected").should("have.value", "")
    cy.get("#searchFg .property_value").eq(1).find("select").select("2")
    cy.get("#searchFg .property_value").eq(1).find("select").find(":selected").should("have.value", "2").and("have.text", "option 2")

    // check box
    cy.get("#searchFg .property_key").eq(2).should("have.text", "Check Box")
    cy.get("#searchFg .property_value").eq(2).find("input").should("not.be.checked")
    cy.get("#searchFg .property_value").eq(2).find("input").click()
    cy.get("#searchFg .property_value").eq(2).find("input").should("be.checked")

    // date box
    cy.get("#searchFg .property_key").eq(3).should("have.text", "Date Box")
    // 直接在input框中输入修改日期
    cy.get("#searchFg .property_value").eq(3).find("input").should("have.value", "")
    cy.get("#searchFg .property_value").eq(3).find("input").type("2023-09-04").should("have.value", "2023-09-04")
    cy.get("#showFg").should("exist").click()
    // 点击calendar_img选择并修改日期
    cy.get(".calendar_img").eq(0).should("exist").click()
    cy.get(".calendar .daysrow .day").eq(4).should("exist").should("have.text", "1").click()
    cy.get("#searchFg .property_value").eq(3).find("input").should("have.value", "2023-09-01")

    // list Box
    cy.get("#searchFg .property_key").eq(4).should("have.text", "List Box")
    // 点击 list box
    cy.get("#searchFg .property_value").eq(4).find('select').invoke("val").should("deep.equal", null)
    cy.get("#searchFg .property_value").eq(4).find("select").select("2")
    cy.get("#searchFg .property_value").eq(4).find("select").invoke("val").should("deep.equal", ["2"])
    cy.get("#searchFg .property_value").eq(4).find("select").select(['2', '4'])
    cy.get("#searchFg .property_value").eq(4).find("select").invoke("val").should("deep.equal", ["2", "4"])
  })
})
