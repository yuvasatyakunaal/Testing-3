export const studentValidationSchema = {
  name: {
    isString: {
      errorMessage: "Must be a string",
    },
    isLength: {
      options: { min: 3 },
      errorMessage: "Must contain atleast 3 characters",
    },
    notEmpty: {
      errorMessage: "Shouldn't be empty",
    },
  },
  roll: {
    isNumeric: {
      errorMessage: "Must be a number",
    },
    notEmpty: {
      errorMessage: "Shouldn't be empty",
    },
  },
  branch: {
    isString: {
      errorMessage: "Must be a string",
    },
    notEmpty: {
      errorMessage: "Shouldn't be empty",
    },
  },
  cgpas: {
    isArray: {
      errorMessage: "Must be an array",
    },
    notEmpty : {
        errorMessage : "Shouldn't be empty"
    }
  },

  secretPassword : {
    isString : {
        errorMessage : "Must be a String"
    },
    notEmpty : {
        errorMessage : "Shouldn't be empty"
    },
    isLength : {
        options : {min : 4, max : 20},
        errorMessage : "Must be atleast 4-20 characters"
    }
  }
};
