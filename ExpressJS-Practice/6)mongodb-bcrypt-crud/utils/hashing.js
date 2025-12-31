import bcrypt from "bcrypt";

const saltRounds = 7;

export const hashSecretPassword = (secretPassword) => {
  const salt = bcrypt.genSaltSync(saltRounds);
  return bcrypt.hashSync(secretPassword, salt);
};
