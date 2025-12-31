// The key names should be as it is function name insdie express-validator (ex : notEmpty, isString, etc...)
// Here we did like for each key from the data, we can keep validation thats why we made 
// (name : .., mainName: ...)

export const createValidationSchema = {
  name: {
    notEmpty: {
      errorMessage: "Name shouldn't be empty",
    },
    isLength: {
      options: { min: 3, max: 15 },
      errorMessage: "Must be atleast 3-15 characters",
    },
    isString: {
      errorMessage: "Must be a string",
    },
  },
  mainName: {
    notEmpty: {
      errorMessage: "Main name shouldn't be empty",
    },
  },
};
