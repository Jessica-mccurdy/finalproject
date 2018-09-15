let form = document.getElementById("order");
            form.onsubmit = function() {

                if (!form.type.value)
                {
                    alert("missing type");
                    return false;
                }
            };
