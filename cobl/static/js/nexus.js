(function(){
  "use strict";
  /**
    Provide client side form logic for nexus exports.
    Relates to issue #146.
    This module is only active on the `/nexus/` page.
  */
  return define(['jquery'], function($){
    if(window.location.pathname === "/nexus/"){
      var excludeLoanword = $('#id_excludeLoanword'),
          excludePllLoan = $('#id_excludePllLoan'),
          includePllLoan = $('#id_includePllLoan');
      //Only enabling *PllLoan checkboxes if ¬excludeLoanword:
      var handleLoanword = function(){
        var checked = excludeLoanword.is(':checked');
        excludePllLoan.prop('disabled', checked);
        includePllLoan.prop('disabled', checked);
      };
      handleLoanword();
      excludeLoanword.change(handleLoanword);
      //Mutual checkboxes:
      excludePllLoan.change(function(){
        if(excludePllLoan.is(':checked')){
          includePllLoan.prop('checked', false);
        }
      });
      includePllLoan.change(function(){
        if(includePllLoan.is(':checked')){
          excludePllLoan.prop('checked', false);
        }
      });
    }
  });
}());
