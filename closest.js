let form = document.getElementById("closest");
            form.onsubmit = function() {

                if (!form.rideid.value)
                {
                    alert("please choose a ride");
                    return false;
                }
            };
