
// ES6
class ShoppingList extends React.Component {
  render() {
    return (
      <div className="shopping-list">
        <h1>List for {this.props.name}</h1>
        <ul>
          <li>Instagram</li>
          <li>WhatsApp</li>
          <li>Oculus</li>
        </ul>
      </div>
    );
  }
}


ReactDOM.render(
    <ShoppingList name="Mike" />,
    document.getElementById('shopping-list')
);


// ES5
var FriendsContainer = React.createClass({
  getInitialState: function(){
    return {
      name: 'Mike Gough',
      friends: ['Jake Lingwall', 'Murphy Randall', 'Merrick Christensen'],
    }
  },
  addFriend: function(friend){
    this.setState({
      friends: this.state.friends.concat([friend])
    });
  },
  render: function(){
    return (
      <div>
        <h3> Name: {this.state.name} </h3>
        <AddFriend addNew={this.addFriend} />
        <ShowList names={this.state.friends} />
      </div>
    )
  }
});

var AddFriend = React.createClass({
  getInitialState: function(){
    return {
      newFriend: ''
    }
  },
  updateNewFriend: function(e){
    this.setState({
      newFriend: e.target.value
    });
  },
  handleAddNew: function(){
    this.props.addNew(this.state.newFriend);
    this.setState({
      newFriend: ''
    });
  },
  render: function(){
    return (
        <div>
          <input type="text" value={this.state.newFriend} onChange={this.updateNewFriend} />
          <button onClick={this.handleAddNew}> Add Friend </button>
        </div>
    );
  }
});

var ShowList = React.createClass({
  render: function(){
    var listItems = this.props.names.map(function(friend){
      return <li> {friend} </li>;
    });
    return (
      <div>
        <h3> Friends </h3>
        <ul>
          {listItems}
        </ul>
      </div>
    )
  }
});

ReactDOM.render(
    <FriendsContainer />,
    document.getElementById('myDiv')
);




/*
var FriendsContainer = React.createClass({
  getInitialState: function() {
      return {
         name: 'Mike Gough',
         friends: ['Ryan Richmond', 'Mike Radockavoich', 'Jeff Claassenn']
       }
  },
  render : function(){
      return (
            <div>
              <h3>Name: {this.state.name} </h3>
              <ShowList names={this.state.friends} />
            </div>
      )
  }
});

var ShowList = React.createClass({
    render: function(){
        var listItems = this.props.names.map(function(friend){
            return <li> {friend} </li>;
        });
        return (
            <div>
                <h3> Friends </h3>
                <ul>
                    {listItems}
                </ul>
            </div>
        )
    }
});

ReactDOM.render(
    <FriendsContainer />,
    document.getElementById('myDiv')
);
*/

/*var MyFirstReactClass = React.createClass({
  getInitialState: function(){
    return {
      username: 'Mike'
    }
  },
  myHandleChangeMethod: function(e){
    this.setState({
      username:e.target.value
    });
  },
  render: function(){
    return (
      <div>
        Hello {this.state.username} <br />
        Change Name: <input type="text" value={this.state.username} onChange={this.myHandleChangeMethod} />
      </div>
    )
  }
});

ReactDOM.render(
  <MyFirstReactClass/>,
  document.getElementById('myDiv')
);
    */