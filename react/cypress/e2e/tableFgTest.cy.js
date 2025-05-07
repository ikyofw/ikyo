/* eslint-disable no-undef */
Cypress.on('uncaught:exception', (err, runnable) => {
  // 返回 false 阻止 Cypress 因这个错误而失败
  return false;
});

describe("tableFg", () => {
  it("table base", () => {
    cy.visit("http://localhost:3000/TableHeaderFooterDemo")

    cy.get("#__u").type("admin");
    cy.get("#__p").type("password");
    cy.get("#__login").click();

    cy.get("#tableFg .fieldgroup_caption").should("have.text", "Header / Footer Demo Table")

    cy.get(".headerColumn").eq(0).find("img").should("have.length", 0)
    cy.get('[id="row_-2 tableFg"]').trigger("mouseenter")
    cy.get(".headerColumn").eq(0).find("img").should("have.length", 4)

    cy.get(".bottomIcons").eq(0).find("img").should("have.length", 0)
    cy.get('[id="row_3 tableFg"]').trigger("mouseenter")
    cy.get(".bottomIcons").eq(0).find("img").should("have.length", 1)
  })

  it("table style", () => {
    cy.visit("http://localhost:3000/TableHeaderFooterDemo")

    cy.get("#__u").type("admin");
    cy.get("#__p").type("password");
    cy.get("#__login").click();

    cy.get('[id="cell_-3_5 tableFg"]').should("have.text", "F5-6")
    cy.get('[id="cell_-3_5 tableFg"]').should("have.css", "color", "rgb(255, 0, 0)")

    cy.get('[id="cell_1_1 tableFg"]').should("have.text", "302")
    cy.get('[id="cell_1_1 tableFg"]').should("have.css", "background-color", "rgb(102, 204, 255)")

    cy.get('[id="row_3 tableFg"]').should("have.css", "height", "50px")

    cy.get('[id="table tableFg"] tbody tr').each(($row) => {
      cy.wrap($row).find("td").eq(2).should("have.css", "fontWeight", "700")
    })
  })

  it("column sorted", () => {
    cy.visit("http://localhost:3000/TableHeaderFooterDemo")

    cy.get("#__u").type("admin");
    cy.get("#__p").type("password");
    cy.get("#__login").click();

    cy.get('[id="cell_-2_0 tableFg"]').find("img").should("not.exist")
    cy.get('[id="cell_0_0 tableFg"]').should("have.text", "101")
    cy.get('[id="cell_1_0 tableFg"]').should("have.text", "301")
    cy.get('[id="cell_2_0 tableFg"]').should("have.text", "201")
    cy.get('[id="cell_3_0 tableFg"]').should("have.text", "401")
    cy.get('[id="cell_-2_0 tableFg"]').dblclick()
    cy.get('[id="cell_-2_0 tableFg"]').find('img[src*="sort_icon_desc.png"]').should("be.visible")
    cy.get('[id="cell_0_0 tableFg"]').should("have.text", "101")
    cy.get('[id="cell_1_0 tableFg"]').should("have.text", "201")
    cy.get('[id="cell_2_0 tableFg"]').should("have.text", "301")
    cy.get('[id="cell_3_0 tableFg"]').should("have.text", "401")
    cy.get('[id="cell_-2_0 tableFg"]').dblclick()
    cy.get('[id="cell_-2_0 tableFg"]').find('img[src*="sort_icon_asc.png"]').should("be.visible")
    cy.get('[id="cell_0_0 tableFg"]').should("have.text", "401")
    cy.get('[id="cell_1_0 tableFg"]').should("have.text", "301")
    cy.get('[id="cell_2_0 tableFg"]').should("have.text", "201")
    cy.get('[id="cell_3_0 tableFg"]').should("have.text", "101")
  })

  it("table filter", () => {
    cy.visit("http://localhost:3000/TableHeaderFooterDemo")

    cy.get("#__u").type("admin");
    cy.get("#__p").type("password");
    cy.get("#__login").click();

    // filter
    cy.get('[id="row_-1 tableFg"]').should("not.exist")
    cy.get('[id="row_-2 tableFg"]').trigger("mouseenter")
    cy.get(".headerColumn").find("img").eq(1).should("have.attr", "src").and("include", "search_button.gif")
    cy.get(".headerColumn").find('img[src*="search_button.gif"]').click()
    cy.get('[id="row_-1 tableFg"]').should("exist")
    cy.get('[id="cell_-1_0 tableFg"] input').should("exist").type("3")
    cy.get('[id="table tableFg"] tbody').find("tr").should("have.length", 1)
    cy.get('[id="cell_0_0 tableFg"]').should("not.exist")
    cy.get('[id="cell_1_0 tableFg"]').should("exist").should("have.text", "301")
    cy.get('[id="cell_4_0 tableFg"]').should("have.text", "301")

    // refresh filter
    cy.get(".filterRow img").should("have.length", 2)
    cy.get(".filterRow img").eq(1).should("have.attr", "src").and("include", "refresh_button.gif")
    cy.get(".filterRow img").eq(1).click()
    cy.get('[id="table tableFg"] tbody').find("tr").should("have.length", 4)

    // hide filter row
    cy.get(".filterRow img").eq(0).should("have.attr", "src").and("include", "cancel_button.gif")
    cy.get('[id="row_-1 tableFg"]').should("exist")
    cy.get(".filterRow img").eq(0).click()
    cy.get('[id="row_-1 tableFg"]').should("not.exist")
  })

  it("table cell", () => {
    cy.visit("http://localhost:3000/TableHeaderFooterDemo")

    cy.get("#__u").type("admin");
    cy.get("#__p").type("password");
    cy.get("#__login").click();

    // 点击cell显示activeCell，点击activeCell进入编辑模式并输入修改单元格内容
    cy.get('[id="cell_0_0 tableFg"]').should("have.text", "101")
    cy.get('[id="cell_0_-1 tableFg"]').should("have.text", "")
    cy.get('[id="cell_0_0 tableFg"]').click()
    cy.get(".Spreadsheet__active-cell").eq(0).click()
    cy.get(".Spreadsheet__active-cell input").eq(0).type("3")
    cy.get("body").click()
    cy.get('[id="cell_0_0 tableFg"]').should("have.text", "1013")
    cy.get('[id="cell_0_-1 tableFg"]').should("have.text", "~")
    cy.get('[id="cell_0_0 tableFg"]').click()
    cy.get(".Spreadsheet__active-cell").eq(0).click()
    cy.get(".Spreadsheet__active-cell input").eq(0).type("{backspace}")
    cy.get("body").click()
    cy.get('[id="cell_0_0 tableFg"]').should("have.text", "101")
    cy.get('[id="cell_0_-1 tableFg"]').should("have.text", "")

    // 点击不可编辑列
    cy.get('[id="cell_0_1 tableFg"]').should("have.text", "102")
    cy.get('[id="cell_0_1 tableFg"]').click()
    cy.get(".Spreadsheet__active-cell").should("not.exist")
    cy.get('[id="cell_0_-1 tableFg"]').should("have.text", "")

    // 点击cell显示activeCell，F2进入编辑模式并输入修改单元格内容
    cy.get('[id="cell_1_2 tableFg"]').should("have.text", "303.00")
    cy.get('[id="cell_1_-1 tableFg"]').should("have.text", "")
    cy.get('[id="cell_1_2 tableFg"]').click()
    cy.get(".Spreadsheet__active-cell").eq(0).trigger("keydown", { key: "F2" })
    cy.get(".Spreadsheet__active-cell input").eq(0).type("8")
    cy.get("body").click()
    cy.get('[id="cell_1_2 tableFg"]').should("have.text", "303.01")
    cy.get('[id="cell_1_-1 tableFg"]').should("have.text", "~")

    // 点击cell显示activeCell，键盘输入直接替换单元格内容
    // cy.get('[id="table tableFg"] tbody tr:nth-child(3) td:nth-of-type(4)').should('have.text', '304.0000');
    // cy.get('[id="table tableFg"] tbody tr:nth-child(3) td:nth-of-type(4)').click()
    // cy.get('.Spreadsheet').eq(0).trigger('keydown', { key: 'z' });
    // cy.get('body').click()
    // cy.get('[id="table tableFg"] tbody tr:nth-child(3) td:nth-of-type(4)').should('have.text', '11.0000');

    // 点击comboBox切换选项
    cy.get('[id="cell_2_5 tableFg"]').should("have.text", "option 2")
    cy.get('[id="cell_2_-1 tableFg"]').should("have.text", "")
    cy.get('[id="cell_2_5 tableFg"]').click()
    cy.get(".Spreadsheet__active-cell").eq(0).click()
    cy.get(".rw-dropdown-list-input").click()
    cy.get('[id="dropdownList_listbox"]').contains("option 3").click()
    cy.get("body").click()
    cy.get('[id="cell_2_5 tableFg"]').should("include.text", "option 3")
    cy.get('[id="cell_2_-1 tableFg"]').should("have.text", "~")

    // 点击checkBox切换选项
    cy.get('[id="cell_0_6 tableFg"]').find('img[src*="checkbox_true.gif"]').should("be.visible")
    cy.get('[id="cell_0_-1 tableFg"]').should("have.text", "")
    cy.get('[id="cell_0_6 tableFg"]').find('img[src*="checkbox_true.gif"]').click()
    cy.get('[id="cell_0_6 tableFg"]').find('img[src*="checkbox_false.gif"]').should("be.visible")
    cy.get('[id="cell_0_-1 tableFg"]').should("have.text", "~")
    cy.get('[id="cell_0_6 tableFg"]').find('img[src*="checkbox_false.gif"]').click()
    cy.get('[id="cell_0_6 tableFg"]').find('img[src*="checkbox_true.gif"]').should("be.visible")
    cy.get('[id="cell_0_-1 tableFg"]').should("have.text", "")

    // 点击cell显示activeCell，键盘输入直接替换dateBox内容
    cy.get('[id="cell_0_7 tableFg"]').should("have.text", "2023-09-06")
    cy.get('[id="cell_0_-1 tableFg"]').should("have.text", "")
    cy.get('[id="cell_0_7 tableFg"]').click()
    cy.get(".Spreadsheet__active-cell").eq(0).click()
    cy.get(".calendar_img").eq(0).should("exist").click()
    cy.get(".calendar .daysrow .day").eq(4).should("exist").should("have.text", "1").click()
    cy.get("body").click()
    cy.get('[id="cell_0_7 tableFg"]').should("have.text", "2023-09-01")
    cy.get('[id="cell_0_-1 tableFg"]').should("have.text", "~")
    cy.get('[id="cell_0_7 tableFg"]').click()
    cy.get(".Spreadsheet__active-cell").eq(0).click()
    cy.get(".Spreadsheet__active-cell input").eq(0).type("11").should("have.value", "2023-09-0111")
    cy.get("body").click()
    cy.get('[id="cell_0_7 tableFg"]').should("have.text", "")
    cy.get('[id="cell_0_-1 tableFg"]').should("have.text", "~")

    // 点击advancedSelection切换选项
    cy.get('[id="cell_0_8 tableFg"]').should("include.text", "New York")
    cy.get('[id="cell_0_8 tableFg"]').find("img").click()
    cy.wait(100).then(() => {
      cy.get(".dialog").should("exist")
      cy.get(".dialog_content").find('img[src*="checkbox_true.gif"]').should("have.length", 1)
      cy.get(".dialog_content").find('img[src*="checkbox_false.gif"]').should("have.length", 9)
      cy.get(".dialog_content").find('img[src*="checkbox_false.gif"]').eq(0).click()
      cy.get(".dialog_content").find('img[src*="checkbox_true.gif"]').should("have.length", 1)
      cy.get(".dialog_content").find('img[src*="checkbox_false.gif"]').should("have.length", 9)
    })
    cy.get(".dialog a").eq(1).should("exist").click()
    cy.get('[id="cell_0_8 tableFg"]').should("include.text", "Los Angeles")

    // 点击buttonCell
    cy.get('[id="cell_0_9 tableFg"]').find("img").click()
    cy.get("#msgBox").should("have.text", "Button Click!")

    // 点击pluginCell
    cy.get('[id="cell_0_10 tableFg"]').find("img").click()
    cy.get("#msgBox").should("have.text", "Plugin Click!")
  })

  it("table header footer", () => {
    cy.visit("http://localhost:3000/TableHeaderFooterDemo")

    cy.get("#__u").type("admin");
    cy.get("#__p").type("password");
    cy.get("#__login").click();
    cy.wait(5000);

    // header
    cy.get('[id="cell_-2_0 tableFg"]').should("have.text", "F1 \n(sum)").should("have.attr", "rowspan", "3").should("have.attr", "colspan", "2")
    cy.get('[id="cell_-2_2 tableFg"]').should("have.text", "F2-4").should("have.attr", "rowspan", "1").should("have.attr", "colspan", "3")
    cy.get('[id="cell_-3_2 tableFg"]').should("have.text", "F2 (\navg\n)").should("have.attr", "rowspan", "2").should("have.attr", "colspan", "1")

    // footer func: sum
    cy.get('[id="cell_4_0 tableFg"]').should("have.text", "1004")
    cy.get('[id="cell_0_0 tableFg"]').click()
    cy.get(".Spreadsheet__active-cell").eq(0).click()
    cy.get(".Spreadsheet__active-cell input").eq(0).type("{backspace}").type("2")
    cy.get("body").click()
    cy.get('[id="cell_4_0 tableFg"]').should("have.text", "1005")

    // footer func: avg
    cy.get('[id="cell_4_2 tableFg"]').should("have.text", "253")
    cy.get('[id="cell_0_2 tableFg"]').click()
    cy.get(".Spreadsheet__active-cell").eq(0).click()
    cy.get(".Spreadsheet__active-cell input").eq(0).type("{backspace}{backspace}{backspace}").type("1")
    cy.get("body").click()
    cy.get('[id="cell_4_2 tableFg"]').should("have.text", "485")

    // footer func: min
    cy.get('[id="cell_4_3 tableFg"]').should("have.text", "104")
    cy.get('[id="cell_0_3 tableFg"]').click()
    cy.get(".Spreadsheet__active-cell").eq(0).click()
    cy.get(".Spreadsheet__active-cell input").eq(0).type("{backspace}{backspace}{backspace}{backspace}{backspace}").type("1")
    cy.get("body").click()
    cy.get('[id="cell_4_3 tableFg"]').should("have.text", "204")

    // footer func: customized func(Get the last string combination of each line as the result)
    cy.get('[id="cell_4_5 tableFg"]').should("have.text", "618")
    cy.get('[id="cell_3_5 tableFg"]').click()
    cy.get(".Spreadsheet__active-cell").eq(0).click()
    cy.get(".rw-dropdown-list-input").click()
    cy.get('[id="dropdownList_listbox"]').contains("option 1").click()
    cy.get("body").click()
    cy.get('[id="cell_4_5 tableFg"]').should("have.text", "724")

    // fixed footer contents
    cy.get('[id="cell_4_8 tableFg"]').should("have.text", "text footer").should("have.attr", "colspan", "2")
  })

  it("add row and delete row", () => {
    cy.visit("http://localhost:3000/TableHeaderFooterDemo")

    cy.get("#__u").type("admin");
    cy.get("#__p").type("password");
    cy.get("#__login").click();
    cy.wait(5000);

    // add row
    cy.get('[id="cell_-2_-2 tableFg"]').find('img[src*="insertline_sbutton.gif"]').should("be.visible")
    cy.get('[id="table tableFg"] tbody').find("tr").should("have.length", 4)
    cy.get('[id="cell_-2_-2 tableFg"]').find('img[src*="insertline_sbutton.gif"]').click()
    cy.get('[id="table tableFg"] tbody').find("tr").should("have.length", 5)
    cy.get('[id="cell_4_-1 tableFg"]').should("have.text", "+")

    // del old row
    cy.get('[id="cell_0_-2 tableFg"]').find('img[src*="delete_sbutton.gif"]').should("be.visible")
    cy.get('[id="cell_0_-1 tableFg"]').should("have.text", "")
    cy.get('[id="table tableFg"] tbody').find("tr").should("have.length", 5)
    cy.get('[id="cell_0_-2 tableFg"]').find('img[src*="delete_sbutton.gif"]').click()
    cy.get('[id="cell_0_-1 tableFg"]').should("have.text", "-")
    cy.get('[id="table tableFg"] tbody').find("tr").should("have.length", 5)

    // del new row
    cy.get('[id="cell_4_-2 tableFg"]').find('img[src*="delete_sbutton.gif"]').should("be.visible")
    cy.get('[id="cell_4_-1 tableFg"]').should("have.text", "+")
    cy.get('[id="table tableFg"] tbody').find("tr").should("have.length", 5)
    cy.get('[id="cell_4_-2 tableFg"]').find('img[src*="delete_sbutton.gif"]').click()
    cy.get('[id="table tableFg"] tbody').find("tr").should("have.length", 4)
  })

  it("paging", () => {
    cy.visit("http://localhost:3000/TableHeaderFooterDemo")

    cy.get("#__u").type("admin");
    cy.get("#__p").type("password");
    cy.get("#__login").click();
    cy.wait(5000);

    // add row
    cy.get('[id="cell_-2_-2 tableFg"]').find('img[src*="insertline_sbutton.gif"]').click()
    cy.get('[id="table tableFg"] tbody').find("tr").should("have.length", 5)
    cy.get('[id="cell_4_9 tableFg"]').find("img").should("not.exist")
    cy.get('[id="cell_4_10 tableFg"]').find("img").should("not.exist")
    cy.get('[id="cell_0_-3 tableFg"]').should("exist")
    cy.get(".PageSelectDiv").should("not.exist")
    cy.get('[id="cell_-2_-2 tableFg"]').find('img[src*="insertline_sbutton.gif"]').click()
    cy.get('[id="table tableFg"] tbody').find("tr").should("have.length", 1)
    cy.get('[id="cell_0_-3 tableFg"]').should("not.exist")
    cy.get('[id="cell_5_-3 tableFg"]').should("exist").should("have.text", "6")
    cy.get(".PageSelectDiv").should("exist").find("img").should("have.length", 4)
    cy.get(".PageSelectDiv").should("exist").find("select").should("have.length", 1)

    // change page
    cy.get(".PageSelectDiv").should("exist").find("img").eq(1).click()
    cy.get('[id="cell_0_-3 tableFg"]').should("exist").should("have.text", "1")
    cy.get('[id="cell_5_-3 tableFg"]').should("not.exist")
    cy.get(".PageSelectDiv").should("exist").find("img").eq(0).click()
    cy.get('[id="cell_5_-3 tableFg"]').should("exist").should("have.text", "6")
    cy.get('[id="cell_1_-3 tableFg"]').should("not.exist")

    // show all and jump to select page
    cy.get(".PageSelectDiv").should("exist").find("img").eq(3).click()
    cy.get('[id="table tableFg"] tbody').find("tr").should("have.length", 6)
    cy.get('[id="cell_0_-3 tableFg"]').should("exist").should("have.text", "1")
    cy.get('[id="cell_5_-3 tableFg"]').should("exist").should("have.text", "6")
    cy.get(".PageSelectDiv").should("exist").find("select").select("2")
    cy.get(".PageSelectDiv").should("exist").find("img").eq(0).click()
    cy.get('[id="cell_5_-3 tableFg"]').should("exist").should("have.text", "6")
    cy.get('[id="cell_1_-3 tableFg"]').should("not.exist")
  })
})
