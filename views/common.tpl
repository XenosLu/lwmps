<div id="sidebar">
  <button id="history" type="button" class="btn btn-default">
    <i class="glyphicon glyphicon-list-alt"></i>
  </button>
</div>
<div id="dialog" class="col-xs-12 col-sm-8 col-md-8 col-lg-7">
  <div id="panel">
    <div class="bg-info panel-title">
      <button type="button" class="close">&times;</button>
      <ul id="navtab" class="nav nav-tabs">
        <li class="active">
          <a href="#tabFrame" data-toggle="tab" onclick="history('/list')">
            <i class="glyphicon glyphicon-list"></i>History
          </a>
        </li>
        <li>
          <a href="#tabFrame" data-toggle="tab" onclick="filelist('/fs/')">
            <i class="glyphicon glyphicon-home"></i>Home dir
          </a>
        </li>
      </ul>
    </div>
    <div id="tabFrame" class="tab-pane fade in">
      <table class="table-striped table-responsive table-condensed">
        <tbody id="list">
        </tbody>
      </table>
    </div>
    <div class="panel-footer">
      <button id="videosize" type="button" class="btn btn-default">orign</button>
      <div id="rate" class="btn-group dropup">
        <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown">
          Rate<span class="caret"></span>
        </button>
        <ul class="dropdown-menu" role="menu">
          <li><a href="#" onclick="rate(0.5)">0.5X</a></li>
          <li><a href="#" onclick="rate(0.75)">0.75X</a></li>
          <li class="divider"></li>
          <li><a href="#" onclick="rate(1)">1X</a></li>
          <li class="divider"></li>
          <li><a href="#" onclick="rate(1.5)">1.5X</a></li>
          <li><a href="#" onclick="rate(2)">2X</a></li>
        </ul>
      </div><!-- #rate .btn-group .dropup -->
      <button id="clear" type="button" class="btn btn-default">Clear History</button>
      <div class="btn-group dropup">
        <button type="button" class="btn btn-default" onClick="if(confirm('Suspend ?'))$.post('/suspend');">
          <i class="glyphicon glyphicon-off"></i>
        </button>
        <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown">
          <span class="caret"></span>
        </button>
        <ul class="dropdown-menu" role="menu">
          <li>
            <a onClick="if(confirm('Shutdown ?'))$.post('/shutdown');">
            <i class="glyphicon glyphicon-off"></i>shutdown</a>
          </li>
          <li>
            <a onClick="if(confirm('Restart ?'))$.post('/restart');">
            <i class="glyphicon glyphicon-off"></i>restart</a>
          </li>
        </ul>
      </div><!-- .btn-group .dropup -->
    </div>
  </div><!-- #panel -->
</div><!-- #dialog -->
