jQuery(function($) {

    $('.draggableTable').each(function(){
      var thistable = $(this)
      $(this).sortable({
          // Only make the .panel-heading child elements support dragging.
          // Omit this to make the entire <li>...</li> draggable.
          handle: '.grabber',
          start: function () {
              $(this).addClass('info');
              $('.grabber').addClass('grabbed');
          },
          stop: function () {
            $('.grabber').removeClass('grabbed');
          },

          update: function() {
              reorderRows(thistable);
          }
      });

    })

    $('a.add_code_button').click(function() {

        addCode($(this).attr('formid'));

    });

    $("form").submit(function(event) {
        $(".draggableTable .moveablerow").each(function() {
            var row = this;
            if ($(row).find("input[name$=-id]").val() == "") {
                // For rows with a blank id (newly added)
                var all_empty = true;
                $(row).find(':input').each(function() {
                    var myclass = $(this).attr('class')
                    if (myclass != 'select2-search__field') {
                      var name = $(this).attr('name').split('-')[2];
                      if (name != 'ORDER' && name != 'DELETE') {
                          // We skip all uppercase ones as they are Django sepcial fields
                          all_empty = all_empty && ($(this).val() == "")
                      }
                    }
                })
                if (all_empty) {
                    // We could delete it, but that might be visually disturbing
                    // So lets just check deleted
                    $(row).find('input[name$=-DELETE]').val('on').prop('checked', 'on');
                }
            }
        })
    });
});

function replacePrefix(element, num_forms) {
  var name = $(element).attr('name')
  var id = $(element).attr('id')

  if (name && name.includes('__prefix__')) {
    var new_name = name.replace('__prefix__', num_forms)
    $(element).attr('name', new_name)
  }

  if (id && id.includes('__prefix__')) {
    var new_id = id.replace('__prefix__', num_forms)
    $(element).attr('id', new_id)
  }

}

function addCode(id) {
    var table = '.draggableTable#' + id;
    var formstage = '.formstage#' + id + ' tr';
    var panelList = $(table);

    new_form = $(formstage).clone();

    //Recreate the date time pickers
    //Get options from the formstage
    if ($(formstage).find('.date').data('DateTimePicker')) {
      var options = $(formstage).find('.date').data('DateTimePicker').options()
      //Initialize all date time objects
      $(new_form).find('.date').each(function() {
          $(this).datetimepicker(options);
      })
    }

    // Remove redundant select2s (they'll be remade when reinserted into the node)
    $(new_form).find('span.select2.select2-container').remove();

    new_form.appendTo(panelList);
    var all_tr = table + ' tr'
    num_forms = $(all_tr).length

    $(new_form).find(':input').each(function() {
        replacePrefix(this, num_forms-1)
    });

    // rename the form entries
    reorderRows(table);
    var total_forms_identifier = 'input[name=' + id + '-TOTAL_FORMS]'
    $(total_forms_identifier).val(num_forms);

}

function renumberRow(row,num) {
    order_fields = $(row).find('input[name$="-ORDER"]')
    if (order_fields.length > 0) {
      order_fields.attr('value',num);
    } else {
      $(row).find('input[name$="-order"]').attr('value', num)
    }
}

function reorderRows(panelList) {

    $('.moveablerow', panelList).each(function(index, elem) {
        renumberRow(this,index);
        $(this).find('input[name$=-DELETE]').attr('title',"Delete item "+index);
    });
}

function addSlot() {
  addCode('slots')
}

function addIdent() {
  addCode('identifiers')
}
