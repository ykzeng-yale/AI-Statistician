local({
  cluster <- parallel::makeForkCluster(2L)
  on.exit(parallel::stopCluster(cluster))
  observations <- parallel::clusterCall(cluster, function() Sys.getpid())
  if (length(unique(unlist(observations))) != 2L) stop("Two distinct local workers are required")
  cat(jsonlite::toJSON(list(worker_count = length(observations), distinct_workers = TRUE),
                       auto_unbox = TRUE), "\n", sep = "")
})
