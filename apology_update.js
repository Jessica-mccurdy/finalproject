let form = document.getElementById("update");
            form.onsubmit = function() {

                if (!form.rideid.value)
                {
                    alert("please choose a ride");
                    return false;
                }
            };
© 2018 GitHub, Inc.
