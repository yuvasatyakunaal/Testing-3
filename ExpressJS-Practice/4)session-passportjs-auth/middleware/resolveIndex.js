const resolveIndexByUserId = (req, res, next) => {
  const {params : { id }} = req;
  const parseId = parseInt(id);
  if (isNaN(parseId)) {
    return res.sendStatus(400);
  }
  const findUserIndex = users.findIndex((user) => user.id == parseId);
  // If user not found
  if (findUserIndex == -1) {
    return res.sendStatus(404);
  }
  req.findUserIndex = findUserIndex;
  next();
}

export default resolveIndexByUserId;