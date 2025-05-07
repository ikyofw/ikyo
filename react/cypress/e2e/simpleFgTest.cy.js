/* eslint-disable no-undef */
Cypress.on("uncaught:exception", (err, runnable) => {
  // 返回 false 阻止 Cypress 因这个错误而失败
  return false
})

describe("simpleFg", () => {
  // auto type
  it("type text", () => {
    cy.visit("http://localhost:3000/SimpleFgDemo")

    cy.get("#__u").type("admin")
    cy.get("#__p").type("password")
    cy.get("#__login").click()
    cy.wait(5000)

    cy.get("#simpleFg").should("exist").should("contain", "SimpleFg")

    // cy.get("#simpleFg .property_key").should("have.length", 8)
    // cy.get("#simpleFg .property_value").should("have.length", 7)

    // Label
    cy.get("#simpleFg .property_key").eq(0).should("have.text", "Label")
    cy.get("#simpleFg .property_value").eq(0).find("input").should("have.value", "Testing simple label")
    cy.get("#simpleFg .property_value").eq(0).find("input").should("not.be.visible")

    // Text Box
    cy.get("#simpleFg .property_key").eq(1).should("have.text", "Text Box")
    cy.get("#simpleFg .property_value").eq(1).find("input").should("have.value", "test text")
    cy.get("#simpleFg .property_value").eq(1).find("input").type(" new text").should("have.value", "test text new text")

    // Textarea
    cy.get("#simpleFg .property_key").eq(2).should("have.text", "Text Area")
    cy.get("#simpleFg .property_value").eq(2).find("textarea").should("have.value", "Testing Text Area")
    cy.get("#simpleFg .property_value").eq(2).find("textarea").type(" add new text").should("have.value", "Testing Text Area add new text")

    // Password
    cy.get("#simpleFg .property_key").eq(3).should("have.text", "Password")
    // cy.get("#simpleFg .property_value").eq(3).find("Password").should("have.value", "")
    const pswInput = cy.get("#simpleFg .property_value").eq(3).get('input[type="password"]')
    pswInput.should("exist").should("have.value", "")
    pswInput.type("123").should("have.value", "123")

    // Combo Box
    cy.get("#simpleFg .property_key").eq(4).should("have.text", "Combo Box")
    cy.get("#simpleFg .property_value").eq(4).find("select").find(":selected").should("have.value", "1").and("have.text", "option 1")
    cy.get("#simpleFg .property_value").eq(4).find("select").select("2")
    cy.get("#simpleFg .property_value").eq(4).find("select").find(":selected").should("have.value", "2").and("have.text", "option 2")

    // List Box
    cy.get("#simpleFg .property_key").eq(5).should("have.text", "List Box")
    cy.get("#simpleFg .property_value").eq(5).find("select").find(":selected").should("have.value", "1").and("have.text", "option 1")
    cy.get("#simpleFg .property_value").eq(5).find("select").select("2")
    cy.get("#simpleFg .property_value").eq(5).find("select").find(":selected").should("have.value", "2").and("have.text", "option 2")

    // // Advanced ComboBox
    // cy.get("#simpleFg .property_key").eq(6).should("have.text", "Advanced ComboBox")
    // const dropdown = cy.get(".dropdown-container")
    // dropdown.should("exist")
    // dropdown.find("span").should("have.text", "option 1")
    // dropdown.click()
    // cy.get("label input").click({ multiple: true })
    // dropdown.click()
    // dropdown.should("have.text", "option 2, option 3")

    // // Advanced Select
    // cy.get("#simpleFg .property_key").eq(7).should("have.text", "Advanced Selection")
    // cy.get("#simpleFg .property_value").eq(6).should("include.text", "ShenZhen")
    // cy.get("#simpleFg .property_value").eq(6).find("img").click()
    // cy.wait(100).then(() => {
    //   cy.get(".dialog").should("exist")
    //   cy.get(".dialog_content").should("include.text", "test message")
    //   cy.get(".dialog_content").find('img[src*="checkbox_true.gif"]').should("have.length", 1)
    //   cy.get(".dialog_content").find('img[src*="checkbox_false.gif"]').should("have.length", 3)
    //   cy.get(".dialog_content").find('img[src*="checkbox_false.gif"]').eq(0).click()
    //   cy.get(".dialog_content").find('img[src*="checkbox_true.gif"]').should("have.length", 1)
    //   cy.get(".dialog_content").find('img[src*="checkbox_false.gif"]').should("have.length", 3)
    // })
    // cy.get(".dialog a").eq(1).should("exist").click()
    // cy.get("#simpleFg .property_value").eq(6).should("include.text", "Singapore1")

    // Check Box (3 options)
    cy.get("#simpleFg .property_key").eq(6).should("have.text", "Check Box (3 options)")
    cy.get("#simpleFg .property_value").eq(6).find("input").invoke("val").should("equal", "true")
    cy.get("#simpleFg .property_value").eq(6).find("input").click()
    cy.get("#simpleFg .property_value").eq(6).find("input").invoke("val").should("equal", "false")

    // Check Box (2 options)
    cy.get("#simpleFg .property_key").eq(7).should("have.text", "Check Box (2 options)")
    cy.get("#simpleFg .property_value").eq(7).find("input").should("be.checked")
    cy.get("#simpleFg .property_value").eq(7).find("input").click()
    cy.get("#simpleFg .property_value").eq(7).find("input").should("not.be.checked")

    // Date Box
    cy.get("#simpleFg .property_key").eq(8).should("have.text", "Date Box")
    // 直接在input框中输入修改日期
    const dateInput = cy.get("#simpleFg .property_value").eq(8).find("input")
    dateInput.should("exist")
    dateInput.should("have.value", "2023-09-04")
    dateInput.type("1").should("have.value", "2023-09-041")
    cy.get("#showFg").should("exist").click()
    cy.get("#simpleFg .property_value").eq(8).should("have.text", "Invalidate format")
    dateInput.clear()
    dateInput.type("2023-09-05").should("have.value", "2023-09-05")
    // 点击calendar_img选择并修改日期
    cy.get(".calendar_img").eq(0).should("exist").click()
    cy.get(".calendar .daysrow .day").eq(4).should("exist").should("have.text", "1").click()
    cy.get("#simpleFg .property_value").eq(8).find("input").should("have.value", "2023-09-01")

    // Check Box (2 options)
    cy.get("#simpleFg .property_key").eq(9).should("have.text", "Advanced Selection")
    cy.get("#simpleFg .property_value").eq(9).find("input").should("have.value", "11")
    cy.get("#simpleFg .property_value").eq(9).get("#schAdvancedSelection_button").click()
    cy.wait(500).then(() => {
      cy.get(".dialog").should("exist")
      cy.get(".dialog_content").find('input').should("have.length", 1).type("new text").should("have.value", "new text")
    })
    cy.get(".dialog a").eq(1).should("exist").click()
    cy.get("#simpleFg .property_value").eq(9).find("input").should("have.value", "new text")
  })
})
