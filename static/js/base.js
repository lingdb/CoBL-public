(function(){
  "use strict";
  define(['jquery','bootstrap'], function($){
    $(function(){$('[data-toggle="tooltip"]').tooltip();});
    $(function(){
      if(window.addEventListener){
        window.addEventListener('DOMContentLoaded', CopyAcross, false);
      }else{
        window.attachEvent('onclick', CopyAcross);
      }
    });
  });

  window.CopyAcross = function(f){
    var f_id_arr = f.id.split('#');
    var f_id = f_id_arr[0];
    var f_src = f_id_arr[1];
    var f_trg = f_id_arr[2];
    var wanted = ['src2translit', 'src2root', 'translit2src', 'phoneMic2phoneTic', 'phoneTic2phoneMic'];
    wanted.find(function(x){
      if(f_id === x){
        document.getElementsByName(f_trg)[0].value = document.getElementsByName(f_src)[0].value;
        return true;
      }
    });
  };

  window.MutexCheckbox = function(f){
    // Unchecking others if checked…
    var f_info = f.name.split('-');
    var f_num = f_info[1];
    var chckbx_list = document.getElementsByClassName('MutexCheckbox');
    Array.prototype.forEach.call(chckbx_list, function(targ_chckbx){
      var targ_chckbx_info = targ_chckbx.name.split('-');
      var targ_chckbx_num = targ_chckbx_info[1];
      if(f.id === targ_chckbx.id) return;
      if(f_num !== targ_chckbx_num) return;
      if(targ_chckbx.checked){
        targ_chckbx.checked = false;
      }
    });
  };

  window.MirrorCognateCheckboxes = function(cbox){
    var checked = cbox.checked,
        cld = cbox.dataset.mirror,
        cboxList = document.getElementsByClassName('loan_event');
    Array.prototype.forEach.call(cboxList, function(c){
      if(cld === c.dataset.mirror){
        if(c.checked !== checked){
          c.checked = checked;
        }
      }
    });
  };
})();
